"""Test end-to-end: config flow, entități, serviciu."""

from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.premierenergy.api import PremierEnergyAuthError
from custom_components.premierenergy.const import CONF_PODS, DOMAIN

from .conftest import POD

P = "ro005e123456789"


async def test_config_flow_creates_entry(hass: HomeAssistant, mock_api) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_EMAIL: "user@example.com", CONF_PASSWORD: "x"}
    )
    # un singur POD -> pasul de selecție e sărit
    assert result["type"] is FlowResultType.CREATE_ENTRY, result
    assert result["options"][CONF_PODS] == [POD]
    await hass.async_block_till_done()
    assert hass.states.get(f"sensor.premierenergy_{P}_total_de_plata") is not None


async def test_config_flow_invalid_auth(hass: HomeAssistant, mock_api) -> None:
    mock_api.authenticate.side_effect = PremierEnergyAuthError("Date de conectare incorecte.")
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_EMAIL: "user@example.com", CONF_PASSWORD: "x"}
    )
    assert result["errors"] == {"base": "invalid_auth"}


async def _setup(hass, mock_api):
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="user@example.com",
        data={CONF_EMAIL: "user@example.com", CONF_PASSWORD: "x"},
        options={CONF_PODS: [POD]},
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_entities(hass: HomeAssistant, mock_api) -> None:
    await _setup(hass, mock_api)
    s = lambda k: hass.states.get(f"sensor.premierenergy_{P}_{k}")  # noqa: E731

    assert s("loc_consum").state == "Str. Test 1, Iasi"
    assert s("loc_consum").attributes["e_factura_activa"] is True
    assert float(s("consum_ultima_luna").state) == 245.0
    assert s("consum_ultima_luna").attributes["luna"] == "octombrie 2026"
    assert float(s("total_de_plata").state) == 170.0
    assert s("total_de_plata").attributes["unit_of_measurement"] == "RON"
    assert s("facturi_neplatite").state == "2"
    assert s("facturi_platite").state == "2"
    # cost pe ani: 2026 = 210.5 + 250 + 80 facturat, 210.5 + 150 plătit; 2025 fără storno
    assert float(s("cost_an_curent").state) == 360.5
    costs = s("cost_an_curent").attributes["cost_anual"]
    assert list(costs) == ["2026", "2025"]
    assert costs["2026"]["facturat"] == 540.5 and costs["2026"]["de_plata"] == 180.0
    assert costs["2025"] == {"facturat": 300.0, "platit": 300.0, "de_plata": 0.0,
                             "facturi": 1, "kwh": None, "lei_pe_kwh": None}
    assert costs["2026"]["lei_pe_kwh"] == round(540.5 / 455, 2)
    assert s("ultima_factura").attributes["numar"] == "900003"
    assert s("ultima_plata").state == "210.5"
    assert s("urmatoarea_scadenta").state != "unknown"
    assert " - " in s("perioada_index").state
    assert hass.states.get(f"binary_sensor.premierenergy_{P}_perioada_index_activa").state == "on"
    assert hass.states.get(f"binary_sensor.premierenergy_{P}_factura_restanta").state == "on"
    assert hass.states.get(f"button.premierenergy_{P}_actualizare") is not None
    # nume prietenos din traduceri
    # testele rulează cu limba engleză; în română numele vine din ro.json
    assert s("total_de_plata").attributes["friendly_name"].endswith("Amount due")


async def test_submit_reading_service(hass: HomeAssistant, mock_api) -> None:
    await _setup(hass, mock_api)
    resp = await hass.services.async_call(
        DOMAIN, "trimite_index", {"pod": POD, "index": 12345},
        blocking=True, return_response=True,
    )
    mock_api.submit_reading.assert_awaited_once_with("456", 12345, POD)
    assert resp["mesaj"] == "Index transmis cu succes"


async def test_auth_failure_starts_reauth(hass: HomeAssistant, mock_api) -> None:
    mock_api.get_locations.side_effect = PremierEnergyAuthError("x")
    entry = MockConfigEntry(
        domain=DOMAIN, unique_id="u",
        data={CONF_EMAIL: "u@example.com", CONF_PASSWORD: "x"}, options={},
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    flows = hass.config_entries.flow.async_progress()
    assert any(f["context"]["source"] == "reauth" for f in flows)


async def test_diagnostics_redacts(hass: HomeAssistant, mock_api) -> None:
    from custom_components.premierenergy.diagnostics import (
        async_get_config_entry_diagnostics,
    )
    entry = await _setup(hass, mock_api)
    diag = await async_get_config_entry_diagnostics(hass, entry)
    text = str(diag)
    assert "Str. Test 1" not in text
    assert "a@b.ro" not in text
    assert POD not in text


async def test_dashboard_templates_render(hass: HomeAssistant, mock_api) -> None:
    """Toate template-urile markdown din dashboard se randează fără erori."""
    from pathlib import Path

    import yaml
    from homeassistant.helpers.template import Template

    await _setup(hass, mock_api)
    src = Path(__file__).parent.parent / "dashboard" / "premierenergy_dashboard.yaml"
    dash = yaml.safe_load(src.read_text().replace("ro005e000000000", P))

    contents: list[str] = []

    def walk(node):
        if isinstance(node, dict):
            if node.get("type") == "markdown":
                contents.append(node["content"])
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)
        elif isinstance(node, str) and node.startswith("sensor.premierenergy_"):
            assert hass.states.get(node) is not None, node

    walk(dash)
    assert len(contents) >= 6
    rendered = [Template(c, hass).async_render(parse_result=False) for c in contents]
    joined = "\n".join(rendered)
    assert "900003" in joined and "octombrie 2026" in joined and "Poți transmite" in joined
    # tabelele markdown trebuie să fie pe linii separate
    assert "| 900003 | 20.11.2026 |" in joined
    assert "|:--|:--|:--|--:|:--|\n| 900003" in joined
    assert "| **2026** | **360.50** | 540.50 | 180.00 | 455 | 1.19 |" in joined
    assert "| **2025** | **300.00** | 300.00 | — | — | — |" in joined
    print(joined)
