"""Buton de actualizare manuală Premier Energy."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import PremierEnergyConfigEntry
from .entity import PremierEnergyEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PremierEnergyConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        PremierEnergyRefreshButton(coordinator, pod) for pod in coordinator.data
    )


class PremierEnergyRefreshButton(PremierEnergyEntity, ButtonEntity):
    _attr_icon = "mdi:refresh"

    def __init__(self, coordinator, pod: str) -> None:
        super().__init__(coordinator, pod, "actualizare", "button")

    async def async_press(self) -> None:
        await self.coordinator.async_request_refresh()
