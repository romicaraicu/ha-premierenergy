"""DataUpdateCoordinator pentru Premier Energy."""

from __future__ import annotations

import asyncio
from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    PremierEnergyApi,
    PremierEnergyAuthError,
    PremierEnergyConnectionError,
    PremierEnergyError,
)
from .const import (
    CONF_PODS,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL_HOURS,
    DOMAIN,
)
from .parser import PodData, build_pod_data, pod_of

_LOGGER = logging.getLogger(__name__)


class PremierEnergyCoordinator(DataUpdateCoordinator[dict[str, PodData]]):
    """Descarcă toate datele contului și le grupează per loc de consum."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, api: PremierEnergyApi) -> None:
        hours = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_HOURS)
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN} ({entry.title})",
            update_interval=timedelta(hours=hours),
        )
        self.api = api
        self.raw: dict[str, Any] = {}

    @property
    def selected_pods(self) -> list[str] | None:
        """POD-urile alese de utilizator (None = toate)."""
        pods = self.config_entry.options.get(CONF_PODS, self.config_entry.data.get(CONF_PODS))
        return pods or None

    async def _async_update_data(self) -> dict[str, PodData]:
        try:
            locations, invoices, consumption = await asyncio.gather(
                self.api.get_locations(),
                self.api.get_invoices(),
                self.api.get_consumption(),
            )
            try:
                unassigned = await self.api.get_unassigned_balance()
            except PremierEnergyConnectionError as err:
                _LOGGER.debug("soldNeasociat indisponibil: %s", err)
                unassigned = []

            pods = [pod_of(loc) for loc in locations if pod_of(loc)]
            if self.selected_pods:
                pods = [p for p in pods if p in self.selected_pods]

            payments: dict[str, Any] = {}
            for pod in pods:
                try:
                    payments[pod] = await self.api.get_recent_payments(pod)
                except PremierEnergyConnectionError as err:
                    _LOGGER.debug("recentPayments indisponibil pentru %s: %s", pod, err)
                    payments[pod] = []
        except PremierEnergyAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except PremierEnergyError as err:
            raise UpdateFailed(str(err)) from err

        self.raw = {
            "locConsum": locations,
            "facturi": invoices,
            "consum": consumption,
            "soldNeasociat": unassigned,
            "recentPayments": payments,
        }
        return {pod: build_pod_data(pod, self.raw) for pod in pods}
