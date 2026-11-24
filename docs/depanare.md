# 🛠️ Depanare

[← Înapoi la README](../README.md)

Ceva nu merge? Pornește de la simptom în tabelul de mai jos. Dacă nu găsești răspunsul, strânge informațiile din [secțiunea de jos](#ce-să-trimiți-când-deschizi-un-issue) și deschide un issue.

## Pornește de la simptom

| Ce vezi | Cauza probabilă | Pași |
|---|---|---|
| *Premier Energy* nu apare la **Adaugă integrare** | fișierele nu sunt la locul lor sau nu ai repornit | [→](#integrarea-nu-apare) |
| Formularul spune *Email sau parolă incorecte* | date greșite sau portalul cere un pas în browser | [→](#login-refuzat) |
| Formularul spune *Nu mă pot conecta* | rețea, portal căzut sau login schimbat | [→](#ce-înseamnă-mesajele-din-log) |
| Notificare *Reautentificare necesară* | parola s-a schimbat | introdu parola nouă direct din notificare |
| Toți senzorii sunt *Indisponibil* | ultima actualizare a eșuat | [→](#senzori-indisponibili) |
| Un senzor e gol (`unknown`) | portalul nu trimite câmpul acela pentru contul tău | [→](#un-senzor-rămâne-gol) |
| `trimite_index` dă eroare | fereastra e închisă sau indexul e respins | [→](#transmiterea-indexului-eșuează) |

---

## Unelte

### 1. Log detaliat

Cea mai rapidă cale: **Setări** → **Dispozitive și servicii** → **Premier Energy** → ⋮ → **Activează jurnalizarea de depanare**. Reprodu problema, apoi dezactivează jurnalizarea; fișierul de log se descarcă automat.

Dacă vrei log detaliat permanent, pune în `configuration.yaml`:

```yaml
logger:
  logs:
    custom_components.premierenergy: debug
```

### 2. Diagnostic

**Setări** → **Dispozitive și servicii** → **Premier Energy** → ⋮ → **Descarcă diagnosticul**. Fișierul are:
- rezumatul pe locuri de consum
- numele câmpurilor primite de la API, fără valori
- starea ultimei actualizări

Adresa, emailul, POD-ul și contractele sunt mascate.

### 3. Test fără Home Assistant

Separă problemele de login de cele din Home Assistant:

```bash
.venv/bin/python tools/test_connection.py
```

Instalarea mediului e descrisă în [instalare.md](instalare.md#1-înainte-să-începi). Cu `--dump folder` scriptul salvează și răspunsurile brute. **Acestea conțin date personale**, așa că nu le publica.

---

## Probleme și soluții

### Integrarea nu apare

1. Verifică dacă există fișierul `/config/custom_components/premierenergy/manifest.json`. Dacă ai copiat manual, nu trebuie să existe un folder în plus, de tipul `custom_components/premierenergy/premierenergy`.
2. Repornește complet Home Assistant. Reîncărcarea YAML nu ajunge.
3. Reîncarcă pagina din browser fără cache (Ctrl/Cmd + Shift + R).
4. Caută în **Setări** → **Sistem** → **Jurnale** după `premierenergy`.

### Login refuzat

- Intră pe app.premierenergy.ro din browser, cu aceleași date.
- Dacă portalul îți cere să accepți termeni, să schimbi parola sau să confirmi emailul, fă-o acolo, apoi reîncearcă în Home Assistant.
- Parolele lipite pot avea un spațiu la final.

### Senzori indisponibili

Senzorii devin *Indisponibil* când ultima citire a datelor a eșuat. Integrarea reîncearcă singură la următorul interval.
1. Apasă **Actualizare date**.
2. Dacă problema rămâne, deschide log-ul și caută `UpdateFailed` sau unul dintre mesajele de mai jos.

### Un senzor rămâne gol

Structura unor răspunsuri poate diferi de la un cont la altul, mai ales la consum și la plățile recente. Descarcă diagnosticul și uită-te la `structura_raspunsuri`:
- `consum_exemplu`: trebuie să aibă `contracte` → `consum`, cu `dataCitire` și `consumMWH`.
- `recentPayments_tip`: tipul răspunsului de plăți (`list` sau `dict`).

Trimite aceste chei într-un issue, fără valorile lor, ca parserul să poată fi adaptat.

### Transmiterea indexului eșuează

- **Transmitere index permisă** trebuie să fie `on`.
- Indexul trebuie să fie un număr întreg, cel puțin egal cu ultimul index facturat.
- Motivul exact dat de Premier Energy apare în textul erorii.

---

## Ce înseamnă mesajele din log

| Mesaj | Ce s-a întâmplat |
|---|---|
| `Autentificare Premier Energy reușită` | login complet reușit |
| `Refresh token eșuat (…), reautentificare` | sesiunea a expirat; integrarea se autentifică din nou. Normal, cam o dată pe zi. |
| `Date de conectare incorecte.` | Premier Energy a refuzat emailul sau parola |
| `Login-ul a cerut un pas suplimentar …` | portalul vrea o acțiune în browser (MFA, termeni, parolă nouă) |
| `Nu am găsit configurația formularului B2C (SETTINGS)` | pagina de login s-a schimbat; e nevoie de o versiune nouă a integrării |
| `Răspuns neașteptat la login (HTTP 400)` | formularul de login sau cookie-urile au fost respinse; probabil tot o schimbare la Premier Energy |
| `Serverul B2C nu a returnat access_token` | autentificarea a mers, dar accesul la API nu a fost acordat |
| `/api/…: HTTP 5xx` | eroare temporară pe serverele Premier Energy |
| `soldNeasociat indisponibil` / `recentPayments indisponibil` | un endpoint opțional nu a răspuns; restul datelor merg normal |

---

## Ce să trimiți când deschizi un issue

- versiunea Home Assistant și versiunea integrării
- ce ai făcut, ce te așteptai să se întâmple și ce s-a întâmplat
- liniile relevante din log, **fără** parolă, adresă sau POD
- fișierul de diagnostic

[Deschide un issue →](https://github.com/romicaraicu/ha-premierenergy/issues/new)
