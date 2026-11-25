"""Fixtures pentru testele integrării Premier Energy."""

from datetime import date, timedelta
from unittest.mock import AsyncMock, patch

import pytest

pytest_plugins = "pytest_homeassistant_custom_component"

POD = "RO005E123456789"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


def sample_raw():
    t = date.today()
    return {
        "locConsum": [{
            "PoD": POD, "Adresa": "Str. Test 1, Iasi", "cont_contract": "000123",
            "CONTR_FURN": "456", "ZZFE_STARE_SERVICIU": "X", "ZZFE_EMAIL": "a@b.ro",
            "perioada_citire_start": (t - timedelta(days=2)).isoformat(),
            "perioada_citire_sfarsit": (t + timedelta(days=3)).isoformat(),
        }],
        "facturi": [
            {"POD": POD, "OPBEL": "000800001", "BLDAT": "2025-06-05", "FAEDN": "2025-06-25",
             "factCurenta": 300, "restPlata": 0},
            {"POD": POD, "OPBEL": "000800002", "BLDAT": "2025-03-05", "factCurenta": -40,
             "restPlata": 0, "DOC_TYPE": "S"},
            {"POD": POD, "OPBEL": "000900001", "BLDAT": "2026-10-05", "FAEDN": "2026-10-25",
             "factCurenta": 210.5, "restPlata": 0, "existaPDF": True},
            {"POD": POD, "OPBEL": "000900002", "BLDAT": "2026-11-05",
             "FAEDN": (t - timedelta(days=1)).isoformat(), "factCurenta": 250, "restPlata": 100},
            {"POD": POD, "OPBEL": "000900003", "BLDAT": "2026-11-20",
             "FAEDN": (t + timedelta(days=10)).isoformat(), "factCurenta": 80, "restPlata": 80},
        ],
        "consum": [{"codlocConsum": POD, "contracte": [{"serviciu": "Furnizare", "consum": [
            {"dataCitire": "2026-09-30", "consumMWH": 0.21},
            {"dataCitire": "2026-10-31", "consumMWH": 0.245},
        ]}]}],
        "soldNeasociat": [{"pod": POD, "sold": -10}],
        "recentPayments": [{"dataPlata": "2026-10-20", "suma": 210.5}],
    }


@pytest.fixture
def mock_api():
    raw = sample_raw()
    with patch(
        "custom_components.premierenergy.PremierEnergyApi", autospec=True
    ) as api_cls, patch(
        "custom_components.premierenergy.config_flow.PremierEnergyApi", new=api_cls
    ):
        api = api_cls.return_value
        api.authenticate = AsyncMock()
        api.get_locations = AsyncMock(return_value=raw["locConsum"])
        api.get_invoices = AsyncMock(return_value=raw["facturi"])
        api.get_consumption = AsyncMock(return_value=raw["consum"])
        api.get_unassigned_balance = AsyncMock(return_value=raw["soldNeasociat"])
        api.get_recent_payments = AsyncMock(return_value=raw["recentPayments"])
        api.submit_reading = AsyncMock(return_value={"message": "Index transmis cu succes"})
        yield api
