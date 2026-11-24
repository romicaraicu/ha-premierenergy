"""Entitate de bază Premier Energy (un device per loc de consum)."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from .const import API_BASE_URL, DOMAIN, MANUFACTURER
from .coordinator import PremierEnergyCoordinator
from .parser import PodData


class PremierEnergyEntity(CoordinatorEntity[PremierEnergyCoordinator]):
    """Entitate legată de un POD."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: PremierEnergyCoordinator, pod: str, key: str, platform: str
    ) -> None:
        super().__init__(coordinator)
        self._pod = pod
        self._attr_translation_key = key
        self._attr_unique_id = f"{pod}_{key}"
        # Entity ID previzibil, folosit și de dashboard-ul inclus:
        # sensor.premierenergy_<pod>_<cheie>
        self.entity_id = f"{platform}.{DOMAIN}_{slugify(pod)}_{key}"
        data = coordinator.data.get(pod)
        address = data.address if data else pod
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, pod)},
            name=f"Premier Energy {address}",
            manufacturer=MANUFACTURER,
            model="Loc de consum",
            serial_number=pod,
            entry_type=DeviceEntryType.SERVICE,
            configuration_url=API_BASE_URL,
        )

    @property
    def pod_data(self) -> PodData | None:
        return (self.coordinator.data or {}).get(self._pod)

    @property
    def available(self) -> bool:
        return super().available and self.pod_data is not None
