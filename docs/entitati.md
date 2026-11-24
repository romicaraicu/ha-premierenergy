# 📋 Referință entități

[← Înapoi la README](../README.md)

Fiecare loc de consum (POD) devine un dispozitiv cu 15 entități. Toate ID-urile au aceeași formă:

```
<platformă>.premierenergy_<pod>_<cheie>
```

`<pod>` e codul POD scris cu litere mici. De exemplu, `RO005E123456789` dă `sensor.premierenergy_ro005e123456789_total_de_plata`. Forma rămâne fixă, ca dashboard-ul și automatizările să poată fi copiate de la un cont la altul.

Pe scurt:

| Grupă | Cheie | Tip | Stare |
|---|---|---|---|
| 🏠 Loc | `loc_consum` | sensor | adresa |
| ⚡ Consum | `consum_ultima_luna` | sensor · energie | kWh |
| | `consum_an_curent` | sensor · energie | kWh |
| 💸 Bani | `total_de_plata` | sensor · monetar | RON |
| | `facturi_neplatite` | sensor | număr facturi |
| | `facturi_platite` | sensor | număr facturi |
| | `ultima_factura` | sensor · monetar | RON |
| | `urmatoarea_scadenta` | sensor · dată | dată |
| | `ultima_plata` | sensor · monetar | RON |
| | `factura_restanta` | binary_sensor · problemă | on / off |
| 🔢 Index | `perioada_index` | sensor | „dd.mm.yyyy - dd.mm.yyyy” |
| | `perioada_index_inceput` | sensor · dată | dată |
| | `perioada_index_sfarsit` | sensor · dată | dată |
| | `perioada_index_activa` | binary_sensor | on / off |
| 🔄 Control | `actualizare` | button | — |

În atribute, datele apar în format ISO (`2026-11-20`), ca să poată fi folosite ușor în template-uri. Sumele sunt în lei, cu două zecimale.

---

## 🏠 Loc de consum

**`sensor.…_loc_consum`**: starea e adresa, așa cum apare în aplicația Premier Energy.

| Atribut | Exemplu | Ce e |
|---|---|---|
| `pod` | `RO005E123456789` | codul locului de consum |
| `adresa` | `Str. Exemplu 10, Iași` | adresa completă |
| `cont_contract` | `123456789` | contul contract (fără zerourile din față) |
| `contract_furnizare` | `987654` | contractul folosit la transmiterea indexului |
| `e_factura_activa` | `true` | ai factură electronică activă |
| `email_e_factura` | `nume@exemplu.ro` | adresa pe care vine e-factura |

---

## ⚡ Consum

Premier Energy raportează consumul **pe perioade de facturare**, de obicei lunare, în MWh. Integrarea îl convertește în kWh.

**`sensor.…_consum_ultima_luna`**: consumul din cea mai recentă perioadă.

| Atribut | Exemplu | Ce e |
|---|---|---|
| `luna` | `octombrie 2026` | luna perioadei, după data citirii |
| `de_la` / `pana_la` | `2026-10-01` / `2026-10-31` | intervalul perioadei |
| `kwh` | `245.0` | consumul perioadei |
| `consum_anual` | `{"2025": 2950.0, "2026": 2410.0}` | total pe fiecare an |
| `istoric` | listă | ultimele 24 de perioade, cea mai nouă prima; fiecare are `luna`, `de_la`, `pana_la`, `kwh` |

**`sensor.…_consum_an_curent`**: suma kWh din anul calendaristic curent. Are același atribut `consum_anual`.

> Senzorii de consum nu au `state_class`, pentru că valorile sunt totaluri lunare, nu un contor care crește continuu. Din acest motiv nu apar în Energy Dashboard.

---

## 💸 Facturi și plăți

### Cum se stabilește statusul unei facturi

Regulile sunt aceleași ca în aplicația web Premier Energy:

```
REVERSED = "X"                         → Stornată       (exclusă din liste)
DOC_TYPE = "S"                         → Storno         (exclusă din liste)
rest de plată lipsă                    → În procesare
valoare negativă sau rest ≤ 0,005 lei  → Plătită
valoare − rest > 0,005 lei             → Parțial plătită
altfel                                 → Neplătită
```

O factură e **restantă** dacă e neplătită sau parțial plătită și scadența a trecut.

### Forma unei facturi în atribute

Senzorii de mai jos descriu facturile mereu cu aceleași câmpuri:

```yaml
numar: "900000003"        # fără zerourile din față
data_emitere: "2026-11-20"
scadenta: "2026-12-04"
valoare: 80.0             # valoarea facturii
rest_plata: 80.0          # cât mai e de plătit
status: "Neplătită"
restanta: false
pdf: true                 # PDF disponibil în portal
```

### Senzorii

**`sensor.…_total_de_plata`** (RON): totalul de plată, calculat ca în aplicație: resturile tuturor facturilor plus soldul neasociat. O valoare negativă înseamnă că ai bani în avans.

| Atribut | Ce e |
|---|---|
| `rest_facturi` | suma resturilor de plată |
| `sold_neasociat` | plăți încă nealocate pe facturi (negativ = credit) |
| `restant` | cât e depășit la scadență |
| `urmatoarea_scadenta` | cea mai apropiată scadență viitoare |
| `facturi_neplatite` | câte facturi mai au rest de plată |

**`sensor.…_facturi_neplatite`**: câte facturi sunt neplătite sau parțial plătite. Atributul `facturi` le conține pe toate; vezi și `total_rest_plata`, `restant`, `urmatoarea_scadenta`.

**`sensor.…_facturi_platite`**: câte facturi plătite are contul. `facturi` cuprinde ultimele 12, iar `ultima_factura_platita` pe cea mai recentă.

**`sensor.…_ultima_factura`** (RON): valoarea celei mai recente facturi (după data emiterii), cu toate câmpurile facturii ca atribute. Când apare o factură nouă, se schimbă atributul `numar`, iar pe asta se poate construi o notificare ([retete.md](retete.md#factură-nouă)).

**`sensor.…_urmatoarea_scadenta`** (dată): cea mai apropiată scadență viitoare a unei facturi neachitate. E `unknown` când nu ai nimic de plată.

**`sensor.…_ultima_plata`** (RON): ultima plată înregistrată de Premier Energy. Atributul `data` arată ziua plății, iar `plati` conține ultimele 12 plăți (`data`, `suma`).

**`binary_sensor.…_factura_restanta`**: `on` dacă cel puțin o factură e restantă. Atributul `restant` dă suma restantă.

---

## 🔢 Transmiterea indexului

Premier Energy acceptă indexul autocitit doar într-o fereastră de câteva zile pe lună. Aceste entități îți arată când e deschisă.

**`sensor.…_perioada_index`**: starea e intervalul, de exemplu `22.11.2026 - 27.11.2026`, sau `Perioadă indisponibilă` dacă portalul nu trimite date.

| Atribut | Exemplu | Ce e |
|---|---|---|
| `inceput` / `sfarsit` | `2026-11-22` / `2026-11-27` | capetele intervalului |
| `activa` | `true` | azi se poate transmite |
| `zile_pana_la_inceput` | `0` | câte zile mai sunt până se deschide |
| `zile_ramase` | `3` | câte zile mai e deschisă |
| `index_transmis` | `false` | dacă portalul raportează că ai transmis deja (poate lipsi) |
| `contract` | `987654` | contractul la care se trimite indexul |

**`sensor.…_perioada_index_inceput`** și **`…_sfarsit`** (dată): aceleași capete, ca senzori de tip dată. Sunt utile în declanșatoare de timp și în carduri de tip calendar.

**`binary_sensor.…_perioada_index_activa`**: `on` cât timp fereastra e deschisă.

### Acțiunea `premierenergy.trimite_index`

| Câmp | Obligatoriu | Ce e |
|---|---|---|
| `pod` | da | POD-ul locului de consum, ex. `RO005E123456789` |
| `index` | da | valoarea de pe contor, număr întreg |

```yaml
action: premierenergy.trimite_index
data:
  pod: RO005E123456789
  index: 12345
response_variable: raspuns   # opțional: raspuns.mesaj = mesajul de la Premier Energy
```

- Integrarea găsește singură contractul de furnizare potrivit.
- După trimitere, datele se reîmprospătează automat.
- Dacă trimiți în afara ferestrei, în log apare un avertisment, iar Premier Energy va respinge de obicei cererea.

---

## 🔄 Actualizare date

**`button.…_actualizare`**: citește imediat toate datele contului, fără să aștepte intervalul configurat. Se aplică tuturor locurilor de consum din cont.
