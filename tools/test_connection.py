#!/usr/bin/env python3
"""Testează conexiunea la Premier Energy fără Home Assistant.

Utilizare:
    python3 -m venv .venv && .venv/bin/pip install aiohttp
    .venv/bin/python tools/test_connection.py            # cere email + parolă
    .venv/bin/python tools/test_connection.py --dump out  # salvează JSON-urile brute

Datele salvate cu --dump conțin informații personale (adresă, POD, contracte).
Nu le publica; trimite doar structura (cheile), dacă e nevoie de depanare.
"""

from __future__ import annotations

import argparse
import asyncio
import getpass
import json
import os
import sys
import types
from pathlib import Path

PKG_DIR = Path(__file__).resolve().parent.parent / "custom_components" / "premierenergy"

# Încărcăm doar api.py + const.py, fără __init__.py (care cere Home Assistant).
_pkg = types.ModuleType("premierenergy")
_pkg.__path__ = [str(PKG_DIR)]
sys.modules["premierenergy"] = _pkg

import aiohttp  # noqa: E402

from premierenergy.api import PremierEnergyApi, PremierEnergyError  # noqa: E402
from premierenergy.parser import build_pod_data  # noqa: E402


def _shape(value, depth=0):
    """Structura unui JSON (chei + tipuri), fără valori personale."""
    if isinstance(value, dict):
        return {k: _shape(v, depth + 1) for k, v in value.items()}
    if isinstance(value, list):
        return [_shape(value[0], depth + 1)] if value else []
    return type(value).__name__


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dump", help="director în care se salvează JSON-urile brute")
    args = parser.parse_args()

    email = os.environ.get("PE_EMAIL") or input("Email: ")
    password = os.environ.get("PE_PASSWORD") or getpass.getpass("Parolă: ")

    async with aiohttp.ClientSession() as session:
        api = PremierEnergyApi(session, email, password)
        try:
            print("→ Autentificare...")
            await api.authenticate()
            print("✓ Autentificat")
            raw = {
                "locConsum": await api.get_locations(),
                "facturi": await api.get_invoices(),
                "consum": await api.get_consumption(),
                "soldNeasociat": await api.get_unassigned_balance(),
            }
            pods = [
                p for p in (
                    (loc.get("PoD") or loc.get("POD") or loc.get("pod"))
                    for loc in raw["locConsum"]
                ) if p
            ]
            raw["recentPayments"] = {
                pod: await api.get_recent_payments(pod) for pod in pods
            }
        except PremierEnergyError as err:
            print(f"✗ {type(err).__name__}: {err}")
            return 1

    print("\n=== Structura răspunsurilor (fără valori) ===")
    print(json.dumps({k: _shape(v) for k, v in raw.items()}, indent=2, ensure_ascii=False))

    print("\n=== Ce va vedea Home Assistant ===")
    for pod in pods:
        data = build_pod_data(pod, raw)
        print(json.dumps(data.summary(), indent=2, ensure_ascii=False, default=str))

    if args.dump:
        out = Path(args.dump)
        out.mkdir(parents=True, exist_ok=True)
        for name, value in raw.items():
            (out / f"{name}.json").write_text(
                json.dumps(value, indent=2, ensure_ascii=False)
            )
        print(f"\nJSON-uri brute salvate în {out.resolve()} (conțin date personale!)")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
