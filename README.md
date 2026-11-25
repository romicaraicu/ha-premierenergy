<div align="center">

# ⚡ Premier Energy pentru Home Assistant

**Consumul, facturile și indexul de la Premier Energy, direct în Home Assistant.**

[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2024.12%2B-41BDF5?logo=homeassistant&logoColor=white)](https://www.home-assistant.io/)
[![Marketplace](https://img.shields.io/badge/Marketplace-Add%20from%20link-41BDF5?logo=homeassistant&logoColor=white)](https://www.home-assistant.io/integrations/marketplace)
[![Release](https://img.shields.io/github/v/release/romicaraicu/ha-premierenergy?color=FF9241)](https://github.com/romicaraicu/ha-premierenergy/releases)
[![Licență MIT](https://img.shields.io/badge/licen%C8%9B%C4%83-MIT-1F446E)](LICENSE.md)

</div>

Dacă ai contract de energie electrică cu Premier Energy și folosești Home Assistant, integrarea asta îți scutește drumul prin aplicația [My Premier Energy](https://app.premierenergy.ro/). Te autentifici o singură dată, cu emailul și parola de acolo. De atunci, consumul lunar, facturile și fereastra de transmitere a indexului apar ca entități obișnuite. Le poți pune pe dashboard, le poți folosi în automatizări sau te poți lăsa notificat de ele.

> [!NOTE]
> Proiect personal, neoficial, fără legătură cu Premier Energy. Citește aceleași date pe care le vezi și tu în aplicația lor web.

---

## Ce afli din Home Assistant

| Întrebarea ta | Unde găsești răspunsul |
|---|---|
| **Cât am consumat luna trecută?** | `Consum ultima lună` (kWh), cu istoric pe 24 de luni |
| **Cât am consumat anul ăsta?** | `Consum an curent` + totaluri pe fiecare an |
| **Am ceva de plată?** | `Total de plată` (lei) și `Facturi neplătite`, cu lista completă |
| **Am vreo factură întârziată?** | senzorul binar `Factură restantă` și `Următoarea scadență` |
| **Ce am plătit deja?** | `Facturi plătite` (ultimele 12) și `Ultima plată` |
| **Cât m-a costat curentul pe fiecare an?** | `Plătit în anul curent` + tabel pe ani: plătit, facturat, kWh, lei/kWh |
| **Când pot transmite indexul?** | `Perioadă transmitere index` + senzorul `Transmitere index permisă` |
| **Ce date are locul de consum?** | `Loc de consum`: adresă, POD, contracte, e-Factură |

Pe lângă senzori ai:
- un buton **Actualizare date**
- acțiunea **`premierenergy.trimite_index`**, prin care trimiți indexul fără să deschizi aplicația
- un **dashboard** gata făcut

---

## Pornire rapidă

**1. Instalează din Marketplace** (Home Assistant 2026.11 sau mai nou)

**Setări** → **Marketplace** → **Add from link** → `romicaraicu/ha-premierenergy` → **Install**

**2. Adaugă contul**

**Setări** → **Dispozitive și servicii** → **Adaugă integrare** → *Premier Energy* → email + parolă

**3. (Opțional) Pune dashboard-ul**

```bash
python3 tools/genereaza_dashboard.py <POD-ul tău>
```

Apoi lipește fișierul generat în *Editorul de configurație brută* al unui panou nou.

Instalarea pe versiuni mai vechi (HACS sau manual), alegerea locurilor de consum și dashboard-ul sunt explicate pe larg în **[docs/instalare.md](docs/instalare.md)**.

---

## Documentație

| Ghid | Ce conține |
|---|---|
| 📦 [Instalare și configurare](docs/instalare.md) | Marketplace, HACS, manual, primul cont, dashboard, dezinstalare |
| 📋 [Referință entități](docs/entitati.md) | Fiecare senzor, cu atributele lui și exemple de valori |
| 🧪 [Rețete](docs/retete.md) | Automatizări gata de copiat și trimiterea indexului din dashboard |
| ❓ [Întrebări](docs/intrebari.md) | Siguranța datelor, statusurile facturilor, limitări |
| 🛠️ [Depanare](docs/depanare.md) | Log-uri, diagnostic, mesaje de eroare și ce înseamnă |
| 🔄 [Actualizare](docs/actualizare.md) | Cum aduci o versiune nouă în HA și cum publici una (commit, tag, release) |
| 📜 [Istoric versiuni](CHANGELOG.md) | Ce s-a schimbat în fiecare versiune |

---

## Cum funcționează

```
 Home Assistant                         Premier Energy
┌──────────────────────┐   login    ┌─────────────────────────┐
│ config flow          │ ─────────▶ │ login.premierenergy.ro  │  Azure AD B2C
│ (email + parolă)     │ ◀───────── │ (OAuth2 + PKCE)         │  → token
└──────────┬───────────┘   token    └─────────────────────────┘
           │ la fiecare 6 h (configurabil)
           ▼
┌──────────────────────┐   Bearer   ┌─────────────────────────┐
│ coordinator          │ ─────────▶ │ app.premierenergy.ro    │
│ → parser → senzori   │ ◀───────── │ /api/locConsum, facturi,│
└──────────────────────┘    JSON    │ consum, recentPayments… │
                                    └─────────────────────────┘
```

- **Autentificarea** urmează exact pașii aplicației web. Sesiunea se reînnoiește singură, iar când expiră complet (cam o dată pe zi), integrarea se autentifică din nou cu datele salvate.
- **Statusurile facturilor** (plătită, parțial plătită, restantă, stornată) folosesc aceleași reguli ca aplicația Premier Energy, ca cifrele să coincidă.
- **Totalul de plată** = resturile de plată ale facturilor + soldul neasociat (avans sau credit).

<details>
<summary><b>Endpoint-uri folosite</b></summary>

| Endpoint | Pentru ce |
|---|---|
| `GET /api/locConsum` | locuri de consum, contracte, perioada de citire |
| `GET /api/facturi` | facturi: număr, emitere, scadență, valoare, rest |
| `GET /api/consum` | istoric consum per contract de furnizare |
| `GET /api/recentPayments?pod=` | plăți recente |
| `GET /api/soldNeasociat` | avans sau credit nealocat |
| `POST /api/readings` | transmitere index |

</details>

<details>
<summary><b>Organizarea codului</b></summary>

```
custom_components/premierenergy/
  api.py            client HTTP: login B2C + apeluri API
  parser.py         transformă JSON-ul în date per loc de consum
  coordinator.py    citește periodic toate datele contului
  config_flow.py    adăugare cont, reautentificare, opțiuni
  entity.py         bază comună (un dispozitiv per POD)
  sensor.py · binary_sensor.py · button.py
  diagnostics.py    export cu datele personale mascate
dashboard/          dashboard Lovelace + grafic ApexCharts opțional
tools/              test de conexiune și generator de dashboard
tests/              teste rulate cu Home Assistant real
```

</details>

---

## Bune de știut

- Datele de consum sunt **lunare**, așa cum le facturează Premier Energy. Nu sunt citiri în timp real și nu apar în Energy Dashboard.
- Dacă activezi autentificarea în doi pași pe cont sau dacă Premier Energy își schimbă pagina de login, logarea automată se oprește până la o actualizare a integrării.
- Datele se reîmprospătează la un interval între 1 și 24 de ore, ca să nu încarce inutil serverele furnizorului.

## Ai găsit o problemă?

Ai găsit o problemă sau ai o idee? Deschide un [issue](https://github.com/romicaraicu/ha-premierenergy/issues). Înainte, șterge din log-uri și din capturi adresa, codul POD și numerele de contract.

## Licență

[MIT](LICENSE.md)
