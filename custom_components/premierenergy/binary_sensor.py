"""Senzori binari Premier Energy."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import PremierEnergyConfigEntry
from .entity import PremierEnergyEntity
from .parser import PodData, iso


@dataclass(frozen=True, kw_only=True)
class PEBinaryDescription(BinarySensorEntityDescription):
    value_fn: Callable[[PodData], bool]


BINARY_SENSORS: tuple[PEBinaryDescription, ...] = (
    PEBinaryDescription(
        key="perioada_index_activa",
        icon="mdi:counter",
        value_fn=lambda d: d.reading_window_open,
    ),
    PEBinaryDescription(
        key="factura_restanta",
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=lambda d: d.overdue_amount > 0,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PremierEnergyConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        PremierEnergyBinarySensor(coordinator, pod, description)
        for pod in coordinator.data
        for description in BINARY_SENSORS
    )


class PremierEnergyBinarySensor(PremierEnergyEntity, BinarySensorEntity):
    entity_description: PEBinaryDescription

    def __init__(self, coordinator, pod: str, description: PEBinaryDescription) -> None:
        super().__init__(coordinator, pod, description.key, "binary_sensor")
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        data = self.pod_data
        return self.entity_description.value_fn(data) if data else None

    @property
    def extra_state_attributes(self) -> dict:
        data = self.pod_data
        if data is None:
            return {}
        if self.entity_description.key == "perioada_index_activa":
            return {"inceput": iso(data.reading_start), "sfarsit": iso(data.reading_end)}
        return {"restant": data.overdue_amount}
