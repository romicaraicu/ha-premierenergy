"""Senzori Premier Energy."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.const import UnitOfEnergy
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import PremierEnergyConfigEntry
from .entity import PremierEnergyEntity
from .parser import PodData, iso

CURRENCY = "RON"
HISTORY_LIMIT = 24
PAID_LIMIT = 12


@dataclass(frozen=True, kw_only=True)
class PESensorDescription(SensorEntityDescription):
    value_fn: Callable[[PodData], Any]
    attrs_fn: Callable[[PodData], dict[str, Any]] | None = None


def _location_attrs(d: PodData) -> dict[str, Any]:
    return {
        "pod": d.pod,
        "adresa": d.address,
        "cont_contract": d.account_contract,
        "contract_furnizare": d.supply_contract,
        "e_factura_activa": d.einvoice_active,
        "email_e_factura": d.location.get("ZZFE_EMAIL") or None,
    }


def _last_consumption_attrs(d: PodData) -> dict[str, Any]:
    last = d.last_consumption
    history = [e.as_attr() for e in reversed(d.consumption)][:HISTORY_LIMIT]
    return {
        **(last.as_attr() if last else {}),
        "consum_anual": d.yearly_consumption(),
        "istoric": history,
    }


def _current_year_kwh(d: PodData) -> float | None:
    totals = d.yearly_consumption()
    if not totals:
        return None
    return totals.get(str(date.today().year), 0.0)


def _balance_attrs(d: PodData) -> dict[str, Any]:
    return {
        "rest_facturi": d.invoices_balance,
        "sold_neasociat": d.unassigned_balance,
        "restant": d.overdue_amount,
        "urmatoarea_scadenta": iso(d.next_due_date),
        "facturi_neplatite": len(d.unpaid_invoices),
    }


def _unpaid_attrs(d: PodData) -> dict[str, Any]:
    return {
        "total_rest_plata": round(sum(i.rest_plata for i in d.unpaid_invoices), 2),
        "restant": d.overdue_amount,
        "urmatoarea_scadenta": iso(d.next_due_date),
        "facturi": [i.as_attr() for i in d.unpaid_invoices],
    }


def _paid_attrs(d: PodData) -> dict[str, Any]:
    paid = d.paid_invoices
    return {
        "ultima_factura_platita": paid[0].as_attr() if paid else None,
        "facturi": [i.as_attr() for i in paid[:PAID_LIMIT]],
    }


def _latest_invoice_attrs(d: PodData) -> dict[str, Any]:
    latest = d.latest_invoice
    return latest.as_attr() if latest else {}


def _payment_attrs(d: PodData) -> dict[str, Any]:
    last = d.last_payment or {}
    return {"data": last.get("data"), "plati": d.payments[:PAID_LIMIT]}


def _reading_attrs(d: PodData) -> dict[str, Any]:
    today = date.today()
    start, end = d.reading_start, d.reading_end
    return {
        "inceput": iso(start),
        "sfarsit": iso(end),
        "activa": d.reading_window_open,
        "zile_pana_la_inceput": (start - today).days if start and start > today else 0,
        "zile_ramase": (end - today).days if end and d.reading_window_open else 0,
        "index_transmis": d.reading_submitted,
        "contract": d.supply_contract or d.account_contract,
    }


SENSORS: tuple[PESensorDescription, ...] = (
    PESensorDescription(
        key="loc_consum",
        icon="mdi:home-lightning-bolt-outline",
        value_fn=lambda d: d.address[:255],
        attrs_fn=_location_attrs,
    ),
    PESensorDescription(
        key="consum_ultima_luna",
        icon="mdi:lightning-bolt",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=0,
        value_fn=lambda d: round(d.last_consumption.kwh, 2) if d.last_consumption else None,
        attrs_fn=_last_consumption_attrs,
    ),
    PESensorDescription(
        key="consum_an_curent",
        icon="mdi:calendar-month-outline",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=0,
        value_fn=_current_year_kwh,
        attrs_fn=lambda d: {"consum_anual": d.yearly_consumption()},
    ),
    PESensorDescription(
        key="total_de_plata",
        icon="mdi:cash-clock",
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement=CURRENCY,
        suggested_display_precision=2,
        value_fn=lambda d: d.total_balance,
        attrs_fn=_balance_attrs,
    ),
    PESensorDescription(
        key="facturi_neplatite",
        icon="mdi:file-alert-outline",
        native_unit_of_measurement="facturi",
        value_fn=lambda d: len(d.unpaid_invoices),
        attrs_fn=_unpaid_attrs,
    ),
    PESensorDescription(
        key="facturi_platite",
        icon="mdi:file-check-outline",
        native_unit_of_measurement="facturi",
        value_fn=lambda d: len(d.paid_invoices),
        attrs_fn=_paid_attrs,
    ),
    PESensorDescription(
        key="ultima_factura",
        icon="mdi:file-document-outline",
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement=CURRENCY,
        suggested_display_precision=2,
        value_fn=lambda d: round(d.latest_invoice.valoare, 2) if d.latest_invoice else None,
        attrs_fn=_latest_invoice_attrs,
    ),
    PESensorDescription(
        key="urmatoarea_scadenta",
        icon="mdi:calendar-alert",
        device_class=SensorDeviceClass.DATE,
        value_fn=lambda d: d.next_due_date,
    ),
    PESensorDescription(
        key="ultima_plata",
        icon="mdi:cash-check",
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement=CURRENCY,
        suggested_display_precision=2,
        value_fn=lambda d: (d.last_payment or {}).get("suma"),
        attrs_fn=_payment_attrs,
    ),
    PESensorDescription(
        key="perioada_index",
        icon="mdi:counter",
        value_fn=lambda d: d.reading_label,
        attrs_fn=_reading_attrs,
    ),
    PESensorDescription(
        key="perioada_index_inceput",
        icon="mdi:calendar-start",
        device_class=SensorDeviceClass.DATE,
        value_fn=lambda d: d.reading_start,
    ),
    PESensorDescription(
        key="perioada_index_sfarsit",
        icon="mdi:calendar-end",
        device_class=SensorDeviceClass.DATE,
        value_fn=lambda d: d.reading_end,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PremierEnergyConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        PremierEnergySensor(coordinator, pod, description)
        for pod in coordinator.data
        for description in SENSORS
    )


class PremierEnergySensor(PremierEnergyEntity, SensorEntity):
    entity_description: PESensorDescription

    def __init__(self, coordinator, pod: str, description: PESensorDescription) -> None:
        super().__init__(coordinator, pod, description.key, "sensor")
        self.entity_description = description
        self._update_values()

    def _update_values(self) -> None:
        data = self.pod_data
        if data is None:
            return
        self._attr_native_value = self.entity_description.value_fn(data)
        attrs_fn = self.entity_description.attrs_fn
        self._attr_extra_state_attributes = attrs_fn(data) if attrs_fn else {}

    @callback
    def _handle_coordinator_update(self) -> None:
        self._update_values()
        super()._handle_coordinator_update()
