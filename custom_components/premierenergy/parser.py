"""Transformă răspunsurile brute ale API-ului în date per loc de consum.

Logica de status a facturilor reproduce aplicația web app.premierenergy.ro.
Modulul nu depinde de Home Assistant (testabil cu tools/test_connection.py).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

from .const import AMOUNT_EPSILON

STATUS_PAID = "platita"
STATUS_PARTIAL = "partial_platita"
STATUS_UNPAID = "neplatita"
STATUS_PENDING = "in_procesare"
STATUS_REVERSED = "stornata"
STATUS_CANCELLATION = "storno"

STATUS_LABELS = {
    STATUS_PAID: "Plătită",
    STATUS_PARTIAL: "Parțial plătită",
    STATUS_UNPAID: "Neplătită",
    STATUS_PENDING: "În procesare",
    STATUS_REVERSED: "Stornată",
    STATUS_CANCELLATION: "Storno",
}

LUNI = [
    "ianuarie", "februarie", "martie", "aprilie", "mai", "iunie",
    "iulie", "august", "septembrie", "octombrie", "noiembrie", "decembrie",
]


# ----------------------------------------------------------------- utilitare
def to_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).replace(" ", "").replace(",", "."))
    except ValueError:
        return None


def parse_date(value: Any) -> date | None:
    """Acceptă ISO (2026-11-15, 2026-11-15T00:00:00Z), dd.mm.yyyy, yyyymmdd."""
    if not value:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip()
    if text.startswith("/Date("):  # format .NET /Date(1700000000000)/
        try:
            return datetime.fromtimestamp(int(text[6:].split(")")[0][:13]) / 1000).date()
        except ValueError:
            return None
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%Y%m%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(text[:10] if fmt != "%Y%m%d" else text[:8], fmt).date()
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def fmt_date(value: date | None) -> str | None:
    return value.strftime("%d.%m.%Y") if value else None


def iso(value: date | None) -> str | None:
    return value.isoformat() if value else None


def pod_of(item: dict[str, Any]) -> str:
    return str(item.get("PoD") or item.get("POD") or item.get("pod") or "").strip()


def _first(item: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if item.get(key) not in (None, ""):
            return item[key]
    return None


# ------------------------------------------------------------------ facturi
def invoice_status(inv: dict[str, Any]) -> str:
    if str(inv.get("REVERSED") or "").strip().upper() == "X":
        return STATUS_REVERSED
    if str(inv.get("DOC_TYPE") or "").strip().upper() == "S":
        return STATUS_CANCELLATION
    rest = to_float(inv.get("restPlata"))
    total = to_float(inv.get("factCurenta")) or 0.0
    if rest is None:
        return STATUS_PENDING
    if total < -AMOUNT_EPSILON or rest <= AMOUNT_EPSILON:
        return STATUS_PAID
    if total - rest > AMOUNT_EPSILON:
        return STATUS_PARTIAL
    return STATUS_UNPAID


@dataclass
class Invoice:
    numar: str
    data_emitere: date | None
    scadenta: date | None
    valoare: float
    rest_plata: float
    status: str
    pdf: bool
    raw: dict[str, Any] = field(repr=False)

    @property
    def restanta(self) -> bool:
        return (
            self.status in (STATUS_UNPAID, STATUS_PARTIAL)
            and self.scadenta is not None
            and self.scadenta < date.today()
        )

    def as_attr(self) -> dict[str, Any]:
        return {
            "numar": self.numar,
            "data_emitere": iso(self.data_emitere),
            "scadenta": iso(self.scadenta),
            "valoare": round(self.valoare, 2),
            "rest_plata": round(self.rest_plata, 2),
            "status": STATUS_LABELS[self.status],
            "restanta": self.restanta,
            "pdf": self.pdf,
        }


def _invoice(inv: dict[str, Any]) -> Invoice:
    return Invoice(
        numar=str(inv.get("OPBEL") or "").lstrip("0") or str(inv.get("OPBEL") or ""),
        data_emitere=parse_date(inv.get("BLDAT")),
        scadenta=parse_date(inv.get("FAEDN")),
        valoare=to_float(inv.get("factCurenta")) or 0.0,
        rest_plata=to_float(inv.get("restPlata")) or 0.0,
        status=invoice_status(inv),
        pdf=bool(inv.get("existaPDF")),
        raw=inv,
    )


# ------------------------------------------------------------------- consum
@dataclass
class ConsumptionEntry:
    data_citire: date | None
    data_start: date | None
    kwh: float
    raw: dict[str, Any] = field(repr=False)

    @property
    def luna(self) -> str:
        ref = self.data_citire or self.data_start
        return f"{LUNI[ref.month - 1]} {ref.year}" if ref else "necunoscut"

    def as_attr(self) -> dict[str, Any]:
        return {
            "luna": self.luna,
            "de_la": iso(self.data_start),
            "pana_la": iso(self.data_citire),
            "kwh": round(self.kwh, 2),
        }


def _consumption_for_pod(pod: str, consum: list[dict[str, Any]]) -> list[ConsumptionEntry]:
    loc = next((c for c in consum or [] if str(c.get("codlocConsum", "")).strip() == pod), None)
    if not loc:
        return []
    contracts = loc.get("contracte") or []
    contract = next((c for c in contracts if c.get("serviciu") == "Furnizare"), None)
    entries = (contract or (contracts[0] if contracts else {})).get("consum") or []
    result: list[ConsumptionEntry] = []
    previous: date | None = None
    parsed = sorted(
        entries, key=lambda e: parse_date(e.get("dataCitire")) or date.min
    )
    for item in parsed:
        citire = parse_date(item.get("dataCitire"))
        mwh = to_float(item.get("consumMWH"))
        kwh = to_float(item.get("consumKWH") or item.get("kWh"))
        if kwh is None:
            kwh = (mwh or 0.0) * 1000
        result.append(
            ConsumptionEntry(
                data_citire=citire,
                data_start=parse_date(item.get("dataStart")) or previous,
                kwh=kwh,
                raw=item,
            )
        )
        previous = citire
    return result


# ------------------------------------------------------------------- plăți
_PAY_AMOUNT_KEYS = ("suma", "Suma", "amount", "Amount", "valoare", "Valoare", "BETRW", "sumaPlatita")
_PAY_DATE_KEYS = ("dataPlata", "DataPlata", "data", "Data", "date", "BUDAT", "dataIncasare")


def _payment_list(payments: Any) -> list[dict[str, Any]]:
    if isinstance(payments, list):
        return [p for p in payments if isinstance(p, dict)]
    if isinstance(payments, dict):
        for value in payments.values():
            if isinstance(value, list):
                return [p for p in value if isinstance(p, dict)]
        return [payments] if payments else []
    return []


def _payment(p: dict[str, Any]) -> dict[str, Any]:
    amount = to_float(_first(p, *_PAY_AMOUNT_KEYS))
    when = parse_date(_first(p, *_PAY_DATE_KEYS))
    if when is None:
        for key, value in p.items():
            if "dat" in key.lower() and parse_date(value):
                when = parse_date(value)
                break
    return {"data": iso(when), "suma": round(amount, 2) if amount is not None else None}


# --------------------------------------------------------------- rezultat
@dataclass
class PodData:
    pod: str
    location: dict[str, Any]
    invoices: list[Invoice]
    consumption: list[ConsumptionEntry]
    payments: list[dict[str, Any]]
    unassigned_balance: float

    # -- loc de consum
    @property
    def address(self) -> str:
        return str(_first(self.location, "Adresa", "adresa", "Denumire") or self.pod)

    @property
    def supply_contract(self) -> str | None:
        value = str(self.location.get("CONTR_FURN") or "").strip()
        return value if value and value != "0" else None

    @property
    def account_contract(self) -> str | None:
        value = str(self.location.get("cont_contract") or "").strip()
        return value.lstrip("0") or None

    @property
    def einvoice_active(self) -> bool:
        return str(self.location.get("ZZFE_STARE_SERVICIU") or "").upper() == "X"

    # -- perioadă index
    @property
    def reading_start(self) -> date | None:
        return parse_date(self.location.get("perioada_citire_start"))

    @property
    def reading_end(self) -> date | None:
        return parse_date(self.location.get("perioada_citire_sfarsit"))

    @property
    def reading_window_open(self) -> bool:
        start, end = self.reading_start, self.reading_end
        return bool(start and end and start <= date.today() <= end)

    @property
    def reading_label(self) -> str:
        start, end = fmt_date(self.reading_start), fmt_date(self.reading_end)
        if start and end:
            return f"{start} - {end}"
        return start or end or "Perioadă indisponibilă"

    @property
    def reading_submitted(self) -> bool | None:
        value = self.location.get("autocitit")
        if value is None:
            return None
        return str(value).strip().upper() in ("X", "1", "TRUE", "DA")

    # -- facturi
    @property
    def active_invoices(self) -> list[Invoice]:
        return [i for i in self.invoices if i.status not in (STATUS_REVERSED, STATUS_CANCELLATION)]

    @property
    def unpaid_invoices(self) -> list[Invoice]:
        return [i for i in self.active_invoices if i.status in (STATUS_UNPAID, STATUS_PARTIAL)]

    @property
    def paid_invoices(self) -> list[Invoice]:
        return [i for i in self.active_invoices if i.status == STATUS_PAID]

    @property
    def latest_invoice(self) -> Invoice | None:
        return self.active_invoices[0] if self.active_invoices else None

    @property
    def invoices_balance(self) -> float:
        return round(sum(i.rest_plata for i in self.invoices), 2)

    @property
    def total_balance(self) -> float:
        """Total de plată, calculat ca în aplicația web (facturi + sold neasociat)."""
        return round(self.invoices_balance + self.unassigned_balance, 2)

    @property
    def overdue_amount(self) -> float:
        return round(sum(i.rest_plata for i in self.unpaid_invoices if i.restanta), 2)

    @property
    def next_due_date(self) -> date | None:
        today = date.today()
        dates = [i.scadenta for i in self.unpaid_invoices if i.scadenta and i.scadenta >= today]
        return min(dates) if dates else None

    # -- consum
    @property
    def last_consumption(self) -> ConsumptionEntry | None:
        return self.consumption[-1] if self.consumption else None

    def yearly_consumption(self) -> dict[str, float]:
        totals: dict[str, float] = {}
        for entry in self.consumption:
            ref = entry.data_citire or entry.data_start
            if ref:
                totals[str(ref.year)] = round(totals.get(str(ref.year), 0.0) + entry.kwh, 2)
        return totals

    # -- plăți
    @property
    def last_payment(self) -> dict[str, Any] | None:
        dated = [p for p in self.payments if p.get("data")]
        if dated:
            return max(dated, key=lambda p: p["data"])
        return self.payments[0] if self.payments else None

    def summary(self) -> dict[str, Any]:
        """Rezumat (folosit de scriptul de test și la diagnostic)."""
        last = self.last_consumption
        latest = self.latest_invoice
        return {
            "pod": self.pod,
            "adresa": self.address,
            "contract_furnizare": self.supply_contract,
            "perioada_index": self.reading_label,
            "perioada_index_activa": self.reading_window_open,
            "consum_ultima_luna_kwh": round(last.kwh, 2) if last else None,
            "luna": last.luna if last else None,
            "consum_anual_kwh": self.yearly_consumption(),
            "total_de_plata_lei": self.total_balance,
            "restant_lei": self.overdue_amount,
            "facturi_neplatite": len(self.unpaid_invoices),
            "facturi_platite": len(self.paid_invoices),
            "ultima_factura": latest.as_attr() if latest else None,
            "ultima_plata": self.last_payment,
        }


def build_pod_data(pod: str, raw: dict[str, Any]) -> PodData:
    """raw: {locConsum, facturi, consum, soldNeasociat, recentPayments: {pod: ...}}"""
    location = next((loc for loc in raw.get("locConsum") or [] if pod_of(loc) == pod), {})
    invoices = [
        _invoice(inv) for inv in raw.get("facturi") or [] if pod_of(inv) == pod
    ]
    invoices.sort(
        key=lambda i: (i.data_emitere or date.min, i.numar), reverse=True
    )
    sold = 0.0
    for item in raw.get("soldNeasociat") or []:
        if str(item.get("pod") or item.get("POD") or "").strip() == pod:
            sold += to_float(item.get("sold")) or 0.0
    payments = [
        _payment(p) for p in _payment_list((raw.get("recentPayments") or {}).get(pod))
    ]
    payments.sort(key=lambda p: p.get("data") or "", reverse=True)
    return PodData(
        pod=pod,
        location=location,
        invoices=invoices,
        consumption=_consumption_for_pod(pod, raw.get("consum") or []),
        payments=payments,
        unassigned_balance=round(sold, 2),
    )
