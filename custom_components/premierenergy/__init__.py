"""Integrarea Premier Energy pentru Home Assistant."""

from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, Platform
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
)
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import PremierEnergyApi, PremierEnergyError
from .const import ATTR_INDEX, ATTR_POD, DOMAIN, SERVICE_SUBMIT_READING
from .coordinator import PremierEnergyCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.BUTTON]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

type PremierEnergyConfigEntry = ConfigEntry[PremierEnergyCoordinator]

SUBMIT_READING_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_POD): cv.string,
        vol.Required(ATTR_INDEX): vol.All(vol.Coerce(int), vol.Range(min=0)),
    }
)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Înregistrează serviciul de transmitere index."""

    async def _submit_reading(call: ServiceCall) -> ServiceResponse:
        pod = call.data[ATTR_POD].strip().upper()
        index = call.data[ATTR_INDEX]
        for entry in hass.config_entries.async_entries(DOMAIN):
            if entry.state is not ConfigEntryState.LOADED:
                continue
            coordinator: PremierEnergyCoordinator = entry.runtime_data
            pod_data = (coordinator.data or {}).get(pod)
            if pod_data is None:
                continue
            contract = pod_data.supply_contract or pod_data.account_contract
            if not contract:
                raise ServiceValidationError(
                    f"Nu am găsit contractul de furnizare pentru {pod}"
                )
            if not pod_data.reading_window_open:
                _LOGGER.warning(
                    "Transmitere index pentru %s în afara perioadei (%s)",
                    pod,
                    pod_data.reading_label,
                )
            try:
                result = await coordinator.api.submit_reading(contract, index, pod)
            except PremierEnergyError as err:
                raise HomeAssistantError(f"Indexul nu a fost transmis: {err}") from err
            await coordinator.async_request_refresh()
            message = (result or {}).get("message") if isinstance(result, dict) else None
            return {"pod": pod, "index": index, "mesaj": message or "Index transmis"}
        raise ServiceValidationError(f"Locul de consum {pod} nu este configurat")

    hass.services.async_register(
        DOMAIN,
        SERVICE_SUBMIT_READING,
        _submit_reading,
        schema=SUBMIT_READING_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: PremierEnergyConfigEntry) -> bool:
    """Configurează o intrare (un cont Premier Energy)."""
    api = PremierEnergyApi(
        async_get_clientsession(hass),
        entry.data[CONF_EMAIL],
        entry.data[CONF_PASSWORD],
    )
    coordinator = PremierEnergyCoordinator(hass, entry, api)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))
    return True


async def _async_options_updated(hass: HomeAssistant, entry: PremierEnergyConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: PremierEnergyConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
