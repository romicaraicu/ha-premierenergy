# Premier Energy — Integrare Home Assistant

[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2024.12%2B-41BDF5?logo=homeassistant&logoColor=white)](https://www.home-assistant.io/)
[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
![Versiune](https://img.shields.io/badge/versiune-0.1.0-orange)

Integrare custom pentru [Home Assistant](https://www.home-assistant.io/) care monitorizează contul de client [My Premier Energy](https://app.premierenergy.ro/): locuri de consum, consum lunar, facturi de plată, facturi plătite, plăți și perioada de transmitere a indexului. Datele vin din API-ul folosit de aplicația oficială `app.premierenergy.ro`.

Integrarea creează un dispozitiv pentru fiecare loc de consum (POD), cu senzori, senzori binari, un buton de actualizare și un serviciu pentru transmiterea indexului. Proiectul include și un **dashboard** gata de folosit.

> ⚠️ Integrarea este neoficială și nu este afiliată cu Premier Energy. Folosește doar contul tău, cu datele tale de autentificare.

---

## Ce face integrarea

- **Loc de consum**: adresă, POD, cont contract, contract de furnizare, stare e-Factură
- **Consum lunar**: consumul din ultima lună (kWh), cu istoric pe 24 de luni și totaluri anuale
- **Consum an curent**: totalul kWh din anul în curs
- **Total de plată**: suma de plată calculată ca în aplicația web (rest facturi + sold neasociat)
- **Facturi de plată**: numărul facturilor neplătite sau parțial plătite, cu lista completă (număr, emitere, scadență, rest de plată, restanță)
- **Facturi plătite**: numărul facturilor plătite, cu ultimele 12 în atribute
- **Ultima factură**: valoarea, scadența și statusul celei mai recente facturi
- **Următoarea scadență**: data celei mai apropiate scadențe neachitate
- **Ultima plată**: suma și data ultimei plăți înregistrate
- **Perioada de transmitere a indexului**: intervalul de autocitire, zile rămase, plus senzori de tip dată pentru început și sfârșit
- **Senzori binari**: „Transmitere index permisă” și „Factură restantă”
- **Buton „Actualizare date”**: forțează citirea imediată a datelor
- **Serviciu `premierenergy.trimite_index`**: transmite indexul autocitit
- **Dashboard** cu carduri standard și un grafic opțional ApexCharts
- **Reautentificare** din interfață dacă parola se schimbă
- **Reconfigurare fără reinstalare**: locurile de consum și intervalul de actualizare se schimbă din OptionsFlow
- **Diagnostic** descărcabil, cu datele personale mascate

---

## Sursa datelor

Datele vin din API-ul REST al portalului `app.premierenergy.ro`:

| Endpoint | Descriere |
|----------|-----------|
| `GET /api/locConsum` | Locuri de consum: POD, adresă, contracte, e-Factură, perioada de citire |
| `GET /api/facturi` | Toate facturile: număr, emitere, scadență, valoare, rest de plată, PDF |
| `GET /api/consum` | Istoric consum per loc de consum și contract de furnizare |
| `GET /api/recentPayments?pod=` | Plățile recente pentru un loc de consum |
| `GET /api/soldNeasociat` | Sold neasociat (avans sau credit) per POD |
| `POST /api/readings` | Transmitere index autocitit |

**Autentificare:** email și parolă prin Azure AD B2C (`login.premierenergy.ro`), cu fluxul OAuth2 Authorization Code + PKCE al aplicației web. Integrarea folosește automat refresh token-ul primit. Când acesta expiră (după aproximativ 24h), face din nou login cu email și parolă, fără intervenția ta.

---

## Instalare

### HACS (recomandat)

1. Deschide HACS în Home Assistant
2. Apasă cele 3 puncte (⋮) din dreapta sus și alege **Custom repositories**
3. Adaugă URL-ul repository-ului tău GitHub (ex. `https://github.com/romicaraicu/ha-premierenergy`)
4. Categorie: **Integration**
5. Apasă **Add**, caută „Premier Energy” și alege **Download**
6. Restartează Home Assistant

### Manual

1. Copiază folderul `custom_components/premierenergy/` în directorul `config/custom_components/` din Home Assistant
2. Restartează Home Assistant

Detalii pas cu pas în [SETUP.md](SETUP.md).

---

## Configurare

### Pasul 1: adaugă integrarea

1. Mergi la **Setări** → **Dispozitive și servicii** → **Adaugă integrare**
2. Caută „**Premier Energy**”
3. Completează formularul:

| Câmp | Descriere |
|------|-----------|
| **Email** | Adresa de email a contului app.premierenergy.ro |
| **Parolă** | Parola contului |

### Pasul 2: locuri de consum

Dacă ai mai multe locuri de consum, alege-le pe cele de monitorizat și intervalul de actualizare (1–24 ore, implicit **6 ore**). Dacă ai un singur loc de consum, pasul acesta e sărit automat.

### Pasul 3: reconfigurare (opțional)

Mergi la **Setări** → **Dispozitive și servicii** → **Premier Energy** → **Configurare** (⚙️). Acolo poți schimba locurile de consum și intervalul. Integrarea se reîncarcă automat, fără restart.

---

## Entități create

Integrarea creează un **dispozitiv** pentru fiecare POD, numit „Premier Energy {adresă}”. Entity ID-urile urmează forma `<platformă>.premierenergy_<pod>_<cheie>`, unde `<pod>` e scris cu litere mici (ex. `ro005e123456789`).

| Entitate | Entity ID | Valoare principală |
|----------|-----------|-------------------|
| Loc de consum | `sensor.premierenergy_{pod}_loc_consum` | Adresa |
| Consum ultima lună | `sensor.premierenergy_{pod}_consum_ultima_luna` | kWh |
| Consum an curent | `sensor.premierenergy_{pod}_consum_an_curent` | kWh |
| Total de plată | `sensor.premierenergy_{pod}_total_de_plata` | RON |
| Facturi neplătite | `sensor.premierenergy_{pod}_facturi_neplatite` | Număr facturi |
| Facturi plătite | `sensor.premierenergy_{pod}_facturi_platite` | Număr facturi |
| Ultima factură | `sensor.premierenergy_{pod}_ultima_factura` | RON |
| Următoarea scadență | `sensor.premierenergy_{pod}_urmatoarea_scadenta` | Dată |
| Ultima plată | `sensor.premierenergy_{pod}_ultima_plata` | RON |
| Perioadă transmitere index | `sensor.premierenergy_{pod}_perioada_index` | „15.11.2026 - 22.11.2026” |
| Început perioadă index | `sensor.premierenergy_{pod}_perioada_index_inceput` | Dată |
| Sfârșit perioadă index | `sensor.premierenergy_{pod}_perioada_index_sfarsit` | Dată |
| Transmitere index permisă | `binary_sensor.premierenergy_{pod}_perioada_index_activa` | on / off |
| Factură restantă | `binary_sensor.premierenergy_{pod}_factura_restanta` | on / off (problemă) |
| Actualizare date | `button.premierenergy_{pod}_actualizare` | Apăsare: reîmprospătare |

---

### Senzor: Loc de consum

**Valoare principală:** adresa locului de consum
**Icon:** `mdi:home-lightning-bolt-outline`

```yaml
pod: "RO005E000000000"
adresa: "Str. Exemplu Nr. 10, Localitatea"
cont_contract: "123456789"
contract_furnizare: "987654"
e_factura_activa: true
email_e_factura: "exemplu@email.ro"
```

---

### Senzor: Consum ultima lună

**Valoare principală:** consumul din ultima perioadă facturată (kWh)
**Icon:** `mdi:lightning-bolt`

```yaml
luna: "octombrie 2026"
de_la: "2026-10-01"
pana_la: "2026-10-31"
kwh: 245.0
consum_anual:
  "2025": 2950.0
  "2026": 2410.0
istoric:            # ultimele 24 de luni, cea mai nouă prima
  - luna: "octombrie 2026"
    de_la: "2026-10-01"
    pana_la: "2026-10-31"
    kwh: 245.0
  - luna: "septembrie 2026"
    ...
```

> Portalul raportează consumul în MWh, iar integrarea îl convertește în kWh.

---

### Senzor: Total de plată

**Valoare principală:** suma totală de plată (RON). O valoare negativă înseamnă credit.
**Icon:** `mdi:cash-clock`

```yaml
rest_facturi: 180.0
sold_neasociat: -10.0
restant: 100.0
urmatoarea_scadenta: "2026-12-04"
facturi_neplatite: 2
```

---

### Senzor: Facturi neplătite

**Valoare principală:** numărul facturilor neplătite sau parțial plătite
**Icon:** `mdi:file-alert-outline`

```yaml
total_rest_plata: 180.0
restant: 100.0
urmatoarea_scadenta: "2026-12-04"
facturi:
  - numar: "900000003"
    data_emitere: "2026-11-20"
    scadenta: "2026-12-04"
    valoare: 80.0
    rest_plata: 80.0
    status: "Neplătită"
    restanta: false
    pdf: true
  - numar: "900000002"
    ...
    status: "Parțial plătită"
    restanta: true
```

Statusurile sunt calculate exact ca în aplicația web: **Plătită**, **Parțial plătită**, **Neplătită**, **În procesare**, **Stornată** și **Storno**. Facturile stornate și documentele de stornare nu intră în liste.

---

### Senzor: Facturi plătite

**Valoare principală:** numărul total de facturi plătite
**Icon:** `mdi:file-check-outline`

```yaml
ultima_factura_platita:
  numar: "900000001"
  data_emitere: "2026-10-05"
  valoare: 210.5
  status: "Plătită"
facturi:     # ultimele 12
  - ...
```

---

### Senzor: Perioadă transmitere index

**Valoare principală:** intervalul de autocitire, ex. „22.11.2026 - 27.11.2026”
**Icon:** `mdi:counter`

```yaml
inceput: "2026-11-22"
sfarsit: "2026-11-27"
activa: true
zile_pana_la_inceput: 0
zile_ramase: 3
index_transmis: false     # dacă portalul raportează informația
contract: "987654"
```

---

### Serviciu: `premierenergy.trimite_index`

Transmite indexul autocitit. Folosește-l doar în perioada de transmitere: în afara ei, portalul refuză de obicei cererea.

```yaml
action: premierenergy.trimite_index
data:
  pod: RO005E000000000
  index: 12345
```

Serviciul întoarce mesajul primit de la Premier Energy (`response_variable`), iar după transmitere datele se reîmprospătează automat.

---

## Dashboard

Folderul [`dashboard/`](dashboard/) conține:

- **`premierenergy_dashboard.yaml`**: un dashboard complet (vizualizare de tip *sections*) cu sumar, transmitere index, facturi de plată, facturi plătite și istoric consum. Folosește **doar carduri standard**, fără HACS.
- **`card_grafic_consum_apexcharts.yaml`**: un grafic opțional cu bare pentru consumul lunar. Necesită [apexcharts-card](https://github.com/RomRider/apexcharts-card) din HACS.

### Instalare dashboard

1. Generează fișierul pentru POD-ul tău:
   ```bash
   python3 tools/genereaza_dashboard.py RO005E123456789
   ```
   Alternativ, înlocuiește manual `ro005e000000000` cu POD-ul tău scris cu litere mici.
2. Mergi la **Setări** → **Panouri de bord** → **Adaugă panou** → **Pornește de la zero** și dă-i numele „Premier Energy”
3. Deschide panoul, apasă ✏️ → ⋮ → **Editor de configurație brută**
4. Lipește conținutul fișierului generat și apasă **Salvează**

### Transmitere index din dashboard

Creează un helper și un script, apoi scoate comentariile de pe cardul marcat în dashboard:

```yaml
# configuration.yaml (sau Setări → Dispozitive și servicii → Ajutoare → Număr)
input_number:
  premierenergy_index:
    name: Index contor
    min: 0
    max: 9999999
    step: 1
    mode: box

# scripts.yaml
premierenergy_trimite_index:
  alias: Premier Energy - trimite index
  sequence:
    - action: premierenergy.trimite_index
      data:
        pod: RO005E000000000
        index: "{{ states('input_number.premierenergy_index') | int }}"
      response_variable: rezultat
    - action: persistent_notification.create
      data:
        title: Premier Energy
        message: "{{ rezultat.mesaj }}"
```

---

## Exemple de automatizări

### Notificare la deschiderea perioadei de transmitere index

```yaml
automation:
  - alias: "Premier Energy - poți transmite indexul"
    triggers:
      - trigger: state
        entity_id: binary_sensor.premierenergy_ro005e000000000_perioada_index_activa
        to: "on"
    actions:
      - action: notify.mobile_app_telefonul_meu
        data:
          title: "Premier Energy"
          message: >
            Poți transmite indexul până pe
            {{ state_attr('sensor.premierenergy_ro005e000000000_perioada_index', 'sfarsit') }}.
```

### Notificare factură nouă

```yaml
automation:
  - alias: "Premier Energy - factură nouă"
    triggers:
      - trigger: state
        entity_id: sensor.premierenergy_ro005e000000000_ultima_factura
        attribute: numar
    conditions:
      - condition: template
        value_template: "{{ trigger.from_state.attributes.numar is defined }}"
    actions:
      - action: notify.mobile_app_telefonul_meu
        data:
          title: "Factură nouă Premier Energy"
          message: >
            {{ states('sensor.premierenergy_ro005e000000000_ultima_factura') }} lei,
            scadentă pe {{ state_attr('sensor.premierenergy_ro005e000000000_ultima_factura', 'scadenta') }}.
```

### Reamintire cu 3 zile înainte de scadență

```yaml
automation:
  - alias: "Premier Energy - scadență apropiată"
    triggers:
      - trigger: time
        at: "09:00:00"
    conditions:
      - condition: template
        value_template: >
          {% set s = states('sensor.premierenergy_ro005e000000000_urmatoarea_scadenta') %}
          {{ s not in ['unknown', 'unavailable'] and (as_datetime(s).date() - now().date()).days == 3 }}
    actions:
      - action: notify.mobile_app_telefonul_meu
        data:
          message: >
            Ai de plată {{ states('sensor.premierenergy_ro005e000000000_total_de_plata') }} lei
            la Premier Energy, scadență în 3 zile.
```

---

## Structura fișierelor

```
custom_components/premierenergy/
├── __init__.py          # Setup/unload, serviciul trimite_index (runtime_data pattern)
├── api.py               # Client async: login Azure AD B2C + API REST
├── parser.py            # Transformare date brute → date per POD (statusuri facturi, consum)
├── coordinator.py       # DataUpdateCoordinator - descarcă toate datele contului
├── config_flow.py       # ConfigFlow + OptionsFlow + reauth
├── entity.py            # Entitate de bază (device per POD)
├── sensor.py            # 12 senzori per POD
├── binary_sensor.py     # 2 senzori binari per POD
├── button.py            # Buton actualizare
├── diagnostics.py       # Export diagnostic (date personale mascate)
├── const.py             # Constante, URL-uri, configurație B2C
├── manifest.json
├── services.yaml
├── strings.json
└── translations/
    ├── en.json
    └── ro.json
dashboard/
├── premierenergy_dashboard.yaml        # Dashboard complet (carduri standard)
└── card_grafic_consum_apexcharts.yaml  # Grafic consum (opțional, HACS)
tools/
├── test_connection.py      # Test conexiune fără Home Assistant
└── genereaza_dashboard.py  # Generează dashboard-ul pentru POD-ul tău
```

---

## Cerințe

- **Home Assistant** 2024.12 sau mai nou
- **HACS** (opțional, pentru instalare ușoară)
- **Cont My Premier Energy** activ (email + parolă) pe [app.premierenergy.ro](https://app.premierenergy.ro/)
- Nicio dependență Python suplimentară

---

## Limitări cunoscute

1. **API neoficial**: integrarea folosește același API ca aplicația web. Dacă Premier Energy schimbă API-ul sau pagina de login, integrarea trebuie actualizată.
2. **Fără MFA sau captcha**: dacă activezi autentificarea în doi pași sau portalul introduce captcha, login-ul automat nu va mai funcționa.
3. **Datele de consum** sunt lunare, la nivel de factură, nu în timp real. Senzorii de consum nu sunt de tip `total_increasing`, deci nu pot fi adăugați direct în Energy Dashboard.
4. **Interval de actualizare** între 1 și 24 de ore (implicit 6), ca să nu suprasolicităm portalul.
5. **Un cont pe intrare**: același email nu poate fi adăugat de două ori.
6. **Structura plăților recente** (`recentPayments`) e dedusă din aplicația web. Dacă senzorul „Ultima plată” rămâne gol, trimite un diagnostic (vezi [DEBUG.md](DEBUG.md)).

---

## Contribuții

Contribuțiile sunt binevenite: deschide un issue sau un pull request.

## Licență

MIT, vezi [LICENSE.md](LICENSE.md).
