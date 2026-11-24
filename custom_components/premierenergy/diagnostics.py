"""Diagnostic Premier Energy (date personale mascate)."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant

from . import PremierEnergyConfigEntry

TO_REDACT = {
    CONF_EMAIL,
    CONF_PASSWORD,
    "Adresa",
    "adresa",
    "Denumire",
    "ZZFE_EMAIL",
    "email_e_factura",
    "Partener",
    "partener",
    "cont_contract",
    "CONTR_FURN",
    "contract_furnizare",
    "VKONT",
    "vertrag",
    "Nume",
    "nume",
    "CNP",
    "telefon",
    "email",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: PremierEnergyConfigEntry
) -> dict[str, Any]:
    coordinator = entry.runtime_data
    pods = {
        f"pod_{i + 1}": data.summary()
        for i, data in enumerate((coordinator.data or {}).values())
    }
    raw = coordinator.raw or {}
    return {
        "entry": async_redact_data(dict(entry.data), TO_REDACT),
        "options": {**entry.options, "pods": len(entry.options.get("pods") or [])},
        "last_update_success": coordinator.last_update_success,
        "rezumat": async_redact_data(
            {k: {**v, "pod": "**REDACTED**"} for k, v in pods.items()}, TO_REDACT
        ),
        "structura_raspunsuri": {
            "locConsum_chei": sorted({k for loc in raw.get("locConsum", []) for k in loc}),
            "facturi_chei": sorted({k for inv in raw.get("facturi", []) for k in inv}),
            "facturi_numar": len(raw.get("facturi", [])),
            "consum_exemplu": async_redact_data(
                (raw.get("consum") or [{}])[0], TO_REDACT | {"codlocConsum"}
            ),
            "recentPayments_tip": {
                "**POD**": type(v).__name__ for v in (raw.get("recentPayments") or {}).values()
            },
        },
    }
