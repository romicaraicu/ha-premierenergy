"""Client API pentru portalul My Premier Energy.

Autentificarea se face prin Azure AD B2C (login.premierenergy.ro), emulând
formularul de login (email + parolă) din fluxul OAuth2 Authorization Code + PKCE
folosit de aplicația web oficială. Modulul nu depinde de Home Assistant,
astfel încât poate fi testat independent (vezi tools/test_connection.py).
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import logging
import re
import secrets
import time
from typing import Any
from urllib.parse import parse_qs, quote, urlparse

import aiohttp

from .const import (
    API_BASE_URL,
    B2C_AUTHORIZE_URL,
    B2C_CLIENT_ID,
    B2C_HOST,
    B2C_ORIGIN,
    B2C_REDIRECT_URI,
    B2C_SCOPES,
    B2C_TOKEN_URL,
)

_LOGGER = logging.getLogger(__name__)

_TIMEOUT = aiohttp.ClientTimeout(total=45)
_USER_AGENT = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Mobile/15E148"
)
_SETTINGS_RE = re.compile(r"var\s+SETTINGS\s*=\s*(\{.*?\});", re.DOTALL)
# Reîmprospătăm tokenul cu 2 minute înainte de expirare
_TOKEN_SAFETY_MARGIN = 120


class PremierEnergyError(Exception):
    """Eroare generică Premier Energy."""


class PremierEnergyAuthError(PremierEnergyError):
    """Credențiale invalide sau sesiune care nu mai poate fi reîmprospătată."""


class PremierEnergyConnectionError(PremierEnergyError):
    """Eroare de rețea sau răspuns neașteptat de la server."""


def _pkce_pair() -> tuple[str, str]:
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(48)).rstrip(b"=").decode()
    challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest())
        .rstrip(b"=")
        .decode()
    )
    return verifier, challenge


def _collect_cookies(resp: aiohttp.ClientResponse, cookies: dict[str, str]) -> None:
    """Preia cookie-urile din Set-Cookie fără a le modifica valoarea."""
    for header in resp.headers.getall("Set-Cookie", []):
        name, _, value = header.split(";", 1)[0].partition("=")
        if name.strip():
            cookies[name.strip()] = value.strip()


def _extract_code(location: str) -> str | None:
    """Extrage parametrul `code` din URL-ul de redirect (query sau fragment)."""
    parsed = urlparse(location)
    for part in (parsed.query, parsed.fragment):
        values = parse_qs(part)
        if "code" in values:
            return values["code"][0]
        if "error" in values:
            desc = values.get("error_description", values["error"])[0]
            raise PremierEnergyAuthError(f"Eroare B2C: {desc}")
    return None


class PremierEnergyApi:
    """Client asincron pentru app.premierenergy.ro."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        email: str,
        password: str,
        token_data: dict[str, Any] | None = None,
    ) -> None:
        self._session = session
        self._email = email
        self._password = password
        self._access_token: str | None = None
        self._refresh_token: str | None = None
        self._expires_at: float = 0
        self._lock = asyncio.Lock()
        if token_data:
            self._access_token = token_data.get("access_token")
            self._refresh_token = token_data.get("refresh_token")
            self._expires_at = float(token_data.get("expires_at", 0))

    # ------------------------------------------------------------------ token
    @property
    def token_data(self) -> dict[str, Any]:
        """Datele de token, pentru a fi persistate între reporniri."""
        return {
            "access_token": self._access_token,
            "refresh_token": self._refresh_token,
            "expires_at": self._expires_at,
        }

    def _store_tokens(self, payload: dict[str, Any]) -> None:
        access = payload.get("access_token")
        if not access:
            raise PremierEnergyAuthError(
                "Serverul B2C nu a returnat access_token (scope API neacordat)"
            )
        self._access_token = access
        if payload.get("refresh_token"):
            self._refresh_token = payload["refresh_token"]
        expires_in = int(payload.get("expires_in") or 3600)
        self._expires_at = time.time() + expires_in

    async def _ensure_token(self, force: bool = False) -> str:
        async with self._lock:
            if (
                not force
                and self._access_token
                and time.time() < self._expires_at - _TOKEN_SAFETY_MARGIN
            ):
                return self._access_token
            if self._refresh_token:
                try:
                    await self._refresh()
                    return self._access_token  # type: ignore[return-value]
                except PremierEnergyAuthError as err:
                    _LOGGER.debug("Refresh token eșuat (%s), reautentificare", err)
            await self._login()
            return self._access_token  # type: ignore[return-value]

    async def _refresh(self) -> None:
        data = {
            "grant_type": "refresh_token",
            "client_id": B2C_CLIENT_ID,
            "refresh_token": self._refresh_token,
            "scope": B2C_SCOPES,
            "redirect_uri": B2C_REDIRECT_URI,
        }
        try:
            async with self._session.post(
                B2C_TOKEN_URL,
                data=data,
                headers={"Origin": B2C_ORIGIN},
                timeout=_TIMEOUT,
            ) as resp:
                payload = await resp.json(content_type=None)
                if resp.status != 200:
                    self._refresh_token = None
                    raise PremierEnergyAuthError(
                        payload.get("error_description", f"HTTP {resp.status}")
                    )
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise PremierEnergyConnectionError(f"Refresh eșuat: {err}") from err
        self._store_tokens(payload)

    async def authenticate(self) -> None:
        """Forțează un login complet (folosit în config flow)."""
        async with self._lock:
            await self._login()

    async def _login(self) -> None:
        """Login complet email/parolă prin formularul Azure AD B2C."""
        verifier, challenge = _pkce_pair()
        params = {
            "client_id": B2C_CLIENT_ID,
            "response_type": "code",
            "redirect_uri": B2C_REDIRECT_URI,
            "response_mode": "query",
            "scope": B2C_SCOPES,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "state": secrets.token_urlsafe(16),
            "nonce": secrets.token_urlsafe(16),
            "prompt": "login",
        }
        headers = {"User-Agent": _USER_AGENT, "Accept-Language": "ro-RO,ro;q=0.9"}
        # Sesiune separată doar pentru login. Cookie-urile B2C (valori base64 cu
        # '=' și '/') sunt gestionate manual: CookieJar-ul aiohttp le pune între
        # ghilimele, iar B2C răspunde atunci cu "Bad Request".
        cookies: dict[str, str] = {}

        def _cookie_header() -> dict[str, str]:
            return {"Cookie": "; ".join(f"{k}={v}" for k, v in cookies.items())}

        try:
            async with aiohttp.ClientSession(
                cookie_jar=aiohttp.DummyCookieJar(), headers=headers, timeout=_TIMEOUT
            ) as login_session:
                # 1. Pagina de login -> SETTINGS (csrf, transId, policy)
                async with login_session.get(B2C_AUTHORIZE_URL, params=params) as resp:
                    for hist in (*resp.history, resp):
                        _collect_cookies(hist, cookies)
                    html = await resp.text()
                    authorize_url = str(resp.url)
                    if resp.status != 200:
                        raise PremierEnergyConnectionError(
                            f"Pagina de login a răspuns HTTP {resp.status}"
                        )
                match = _SETTINGS_RE.search(html)
                if not match:
                    raise PremierEnergyConnectionError(
                        "Nu am găsit configurația formularului B2C (SETTINGS)"
                    )
                settings = json.loads(match.group(1))
                csrf = settings["csrf"]
                trans_id = settings["transId"]
                tenant_path = settings["hosts"]["tenant"]
                policy = settings["hosts"]["policy"]
                base = f"{B2C_HOST}{tenant_path}"
                qs = f"tx={trans_id}&p={policy}"

                # 2. Trimitem email + parolă
                async with login_session.post(
                    f"{base}/SelfAsserted?{qs}",
                    data={
                        "request_type": "RESPONSE",
                        "signInName": self._email,
                        "password": self._password,
                    },
                    headers={
                        "X-CSRF-TOKEN": csrf,
                        "X-Requested-With": "XMLHttpRequest",
                        "Referer": authorize_url,
                        "Accept": "application/json, text/javascript, */*; q=0.01",
                        **_cookie_header(),
                    },
                ) as resp:
                    _collect_cookies(resp, cookies)
                    raw = await resp.text()
                try:
                    result = json.loads(raw)
                except ValueError as err:
                    raise PremierEnergyConnectionError(
                        f"Răspuns neașteptat la login (HTTP {resp.status})"
                    ) from err
                if str(result.get("status")) != "200":
                    raise PremierEnergyAuthError(
                        result.get("message") or "Email sau parolă incorecte"
                    )

                # 3. Confirmare -> redirect cu ?code=
                async with login_session.get(
                    f"{base}/api/CombinedSigninAndSignup/confirmed",
                    params={
                        "rememberMe": "false",
                        "csrf_token": csrf,
                        "tx": trans_id,
                        "p": policy,
                    },
                    headers={"Referer": authorize_url, **_cookie_header()},
                    allow_redirects=False,
                ) as resp:
                    location = resp.headers.get("Location", "")
                    status = resp.status
                code = _extract_code(location) if location else None
                if not code:
                    raise PremierEnergyAuthError(
                        "Login-ul a cerut un pas suplimentar (ex. MFA, schimbare parolă "
                        f"sau acceptare termeni) - HTTP {status}. Autentifică-te o dată "
                        "în aplicația web și încearcă din nou."
                    )

                # 4. Schimbăm codul pe tokenuri
                async with login_session.post(
                    B2C_TOKEN_URL,
                    data={
                        "grant_type": "authorization_code",
                        "client_id": B2C_CLIENT_ID,
                        "code": code,
                        "redirect_uri": B2C_REDIRECT_URI,
                        "code_verifier": verifier,
                        "scope": B2C_SCOPES,
                    },
                    headers={"Origin": B2C_ORIGIN},
                ) as resp:
                    payload = await resp.json(content_type=None)
                    if resp.status != 200:
                        raise PremierEnergyAuthError(
                            payload.get("error_description", f"HTTP {resp.status}")
                        )
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise PremierEnergyConnectionError(f"Eroare de conexiune: {err}") from err
        except (KeyError, ValueError) as err:
            raise PremierEnergyConnectionError(
                f"Formularul de login B2C s-a schimbat: {err}"
            ) from err
        self._store_tokens(payload)
        _LOGGER.debug("Autentificare Premier Energy reușită")

    # -------------------------------------------------------------------- API
    async def _request(
        self, method: str, path: str, *, json_body: Any = None, raw: bool = False
    ) -> Any:
        for attempt in (1, 2):
            token = await self._ensure_token(force=attempt == 2)
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
            }
            try:
                async with self._session.request(
                    method,
                    f"{API_BASE_URL}{path}",
                    json=json_body,
                    headers=headers,
                    timeout=_TIMEOUT,
                ) as resp:
                    if resp.status == 401 and attempt == 1:
                        continue
                    if resp.status == 401:
                        raise PremierEnergyAuthError("API a refuzat tokenul (401)")
                    if raw:
                        if resp.status >= 400:
                            raise PremierEnergyConnectionError(
                                f"{path}: HTTP {resp.status}"
                            )
                        return await resp.read(), resp.headers.get("Content-Type", "")
                    text = await resp.text()
                    if resp.status >= 400:
                        raise PremierEnergyConnectionError(
                            f"{path}: HTTP {resp.status} {text[:200]}"
                        )
                    return json.loads(text) if text else None
            except (aiohttp.ClientError, asyncio.TimeoutError) as err:
                raise PremierEnergyConnectionError(f"{path}: {err}") from err
            except ValueError as err:
                raise PremierEnergyConnectionError(f"{path}: JSON invalid") from err
        raise PremierEnergyAuthError("Autentificare eșuată")

    async def get_locations(self) -> list[dict[str, Any]]:
        """Locurile de consum (PoD, Adresa, cont_contract, perioada_citire_*...)."""
        return await self._request("GET", "/api/locConsum") or []

    async def get_invoices(self) -> list[dict[str, Any]]:
        """Toate facturile (OPBEL, BLDAT, FAEDN, factCurenta, restPlata, POD...)."""
        return await self._request("GET", "/api/facturi") or []

    async def get_consumption(self) -> list[dict[str, Any]]:
        """Consum: [{codlocConsum, contracte: [{serviciu, consum: [...]}]}]."""
        return await self._request("GET", "/api/consum") or []

    async def get_recent_payments(self, pod: str) -> Any:
        """Plățile recente pentru un loc de consum."""
        return await self._request("GET", f"/api/recentPayments?pod={quote(pod)}")

    async def get_unassigned_balance(self) -> list[dict[str, Any]]:
        """Sold neasociat per POD ([{pod, sold}])."""
        return await self._request("GET", "/api/soldNeasociat") or []

    async def submit_reading(
        self, contract: str, index: int, pod: str | None = None
    ) -> Any:
        """Transmite indexul autocitit."""
        body: dict[str, Any] = {"contract": contract, "index": int(index)}
        if pod:
            body["pod"] = pod
        return await self._request("POST", "/api/readings", json_body=body)

    async def get_invoice_pdf(self, invoice_number: str) -> bytes:
        """Descarcă PDF-ul unei facturi (serverul poate returna base64 sau binar)."""
        content, content_type = await self._request(
            "GET", f"/api/facturi/{quote(invoice_number)}/pdf", raw=True
        )
        if "text" in content_type or "json" in content_type:
            text = content.decode().strip().strip('"')
            return base64.b64decode(text)
        return content
