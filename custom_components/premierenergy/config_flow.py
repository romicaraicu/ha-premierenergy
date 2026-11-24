"""Config flow pentru Premier Energy."""

from __future__ import annotations

from collections.abc import Mapping
import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api import PremierEnergyApi, PremierEnergyAuthError, PremierEnergyError
from .const import (
    CONF_PODS,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL_HOURS,
    DOMAIN,
    MAX_SCAN_INTERVAL_HOURS,
    MIN_SCAN_INTERVAL_HOURS,
)
from .parser import pod_of

_LOGGER = logging.getLogger(__name__)

CREDENTIALS_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): TextSelector(
            TextSelectorConfig(type=TextSelectorType.EMAIL, autocomplete="username")
        ),
        vol.Required(CONF_PASSWORD): TextSelector(
            TextSelectorConfig(
                type=TextSelectorType.PASSWORD, autocomplete="current-password"
            )
        ),
    }
)


def _interval_selector() -> NumberSelector:
    return NumberSelector(
        NumberSelectorConfig(
            min=MIN_SCAN_INTERVAL_HOURS,
            max=MAX_SCAN_INTERVAL_HOURS,
            step=1,
            unit_of_measurement="h",
            mode=NumberSelectorMode.SLIDER,
        )
    )


def _pods_selector(locations: list[dict[str, Any]]) -> SelectSelector:
    options = []
    for loc in locations:
        pod = pod_of(loc)
        if not pod:
            continue
        label = loc.get("Adresa") or loc.get("Denumire") or pod
        options.append(SelectOptionDict(value=pod, label=f"{label} ({pod})"))
    return SelectSelector(
        SelectSelectorConfig(
            options=options, multiple=True, mode=SelectSelectorMode.LIST
        )
    )


async def _validate(hass, email: str, password: str) -> list[dict[str, Any]]:
    """Autentifică și întoarce locurile de consum."""
    api = PremierEnergyApi(async_get_clientsession(hass), email, password)
    await api.authenticate()
    return await api.get_locations()


class PremierEnergyConfigFlow(ConfigFlow, domain=DOMAIN):
    """Fluxul de adăugare a unui cont Premier Energy."""

    VERSION = 1

    def __init__(self) -> None:
        self._email: str = ""
        self._password: str = ""
        self._locations: list[dict[str, Any]] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            self._email = user_input[CONF_EMAIL].strip()
            self._password = user_input[CONF_PASSWORD]
            await self.async_set_unique_id(self._email.lower())
            self._abort_if_unique_id_configured()
            try:
                self._locations = await _validate(self.hass, self._email, self._password)
            except PremierEnergyAuthError as err:
                _LOGGER.debug("Autentificare eșuată: %s", err)
                errors["base"] = "invalid_auth"
            except PremierEnergyError as err:
                _LOGGER.warning("Nu mă pot conecta la Premier Energy: %s", err)
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Eroare neașteptată")
                errors["base"] = "unknown"
            else:
                if not any(pod_of(loc) for loc in self._locations):
                    errors["base"] = "no_locations"
                else:
                    return await self.async_step_pods()

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(
                CREDENTIALS_SCHEMA, {CONF_EMAIL: self._email}
            ),
            errors=errors,
        )

    async def async_step_pods(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        all_pods = [pod_of(loc) for loc in self._locations if pod_of(loc)]
        if user_input is not None or len(all_pods) == 1:
            pods = (user_input or {}).get(CONF_PODS) or all_pods
            return self.async_create_entry(
                title=self._email,
                data={
                    CONF_EMAIL: self._email,
                    CONF_PASSWORD: self._password,
                },
                options={
                    CONF_PODS: pods,
                    CONF_SCAN_INTERVAL: (user_input or {}).get(
                        CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_HOURS
                    ),
                },
            )
        return self.async_show_form(
            step_id="pods",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_PODS, default=all_pods): _pods_selector(
                        self._locations
                    ),
                    vol.Required(
                        CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL_HOURS
                    ): _interval_selector(),
                }
            ),
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        self._email = entry_data[CONF_EMAIL]
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                await _validate(self.hass, self._email, user_input[CONF_PASSWORD])
            except PremierEnergyAuthError:
                errors["base"] = "invalid_auth"
            except PremierEnergyError:
                errors["base"] = "cannot_connect"
            else:
                return self.async_update_reload_and_abort(
                    self._get_reauth_entry(),
                    data_updates={CONF_PASSWORD: user_input[CONF_PASSWORD]},
                )
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_PASSWORD): TextSelector(
                        TextSelectorConfig(type=TextSelectorType.PASSWORD)
                    )
                }
            ),
            description_placeholders={"email": self._email},
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return PremierEnergyOptionsFlow()


class PremierEnergyOptionsFlow(OptionsFlow):
    """Reconfigurare: locuri de consum și interval de actualizare."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(
                data={**self.config_entry.options, **user_input}
            )

        coordinator = getattr(self.config_entry, "runtime_data", None)
        locations = (coordinator.raw.get("locConsum") if coordinator else None) or []
        current_pods = self.config_entry.options.get(CONF_PODS) or [
            pod_of(loc) for loc in locations if pod_of(loc)
        ]
        schema: dict[Any, Any] = {}
        if locations:
            schema[vol.Required(CONF_PODS, default=current_pods)] = _pods_selector(
                locations
            )
        schema[
            vol.Required(
                CONF_SCAN_INTERVAL,
                default=self.config_entry.options.get(
                    CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_HOURS
                ),
            )
        ] = _interval_selector()
        return self.async_show_form(step_id="init", data_schema=vol.Schema(schema))
