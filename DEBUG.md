# DEBUG: ghid de depanare

---

## Activare log-uri de debug

**Din interfață:** **Setări** → **Dispozitive și servicii** → **Premier Energy** → ⋮ → **Activează jurnalizarea de depanare**. Reprodu problema, apoi dezactivează jurnalizarea; Home Assistant descarcă automat fișierul de log.

**Din `configuration.yaml`:**

```yaml
logger:
  default: warning
  logs:
    custom_components.premierenergy: debug
```

Restartează Home Assistant și urmărește **Setări** → **Sistem** → **Jurnale**.

---

## Descărcare diagnostic

**Setări** → **Dispozitive și servicii** → **Premier Energy** → ⋮ → **Descarcă diagnosticul**.

Fișierul conține:

- rezumatul datelor per loc de consum (consum, totaluri, perioada de index)
- **structura** răspunsurilor API: cheile JSON, fără valori
- starea ultimei actualizări

Adresa, emailul, numerele de contract și POD-ul sunt mascate.

---

## Test în afara Home Assistant

Cel mai rapid mod de a separa o problemă de login de una de Home Assistant:

```bash
python3 -m venv .venv
```

```bash
.venv/bin/pip install aiohttp
```

```bash
.venv/bin/python tools/test_connection.py
```

Cu `--dump director` salvezi și JSON-urile brute. Acestea **conțin date personale**, așa că nu le publica.

---

## Probleme frecvente

### Integrarea nu apare în lista de integrări

- Verifică structura: `config/custom_components/premierenergy/manifest.json` trebuie să existe
- Restartează Home Assistant (nu doar reîncărcare YAML)
- Golește cache-ul browserului (Ctrl+F5)
- Caută în log: `Error loading custom_components.premierenergy`

### „Email sau parolă incorecte” la configurare

- Verifică datele pe app.premierenergy.ro în browser
- Dacă portalul cere un pas suplimentar (termeni noi, schimbare parolă), finalizează-l în browser
- Ai grijă la spațiile de la final când copiezi parola

### „Nu mă pot conecta la Premier Energy”

În log apare cauza exactă. Mesaje posibile:

| Mesaj în log | Cauză |
|--------------|-------|
| `Eroare de conexiune` / `Timeout` | Rețea sau portal indisponibil |
| `Nu am găsit configurația formularului B2C (SETTINGS)` | Pagina de login s-a schimbat; integrarea trebuie actualizată |
| `Răspuns neașteptat la login (HTTP 400)` | Formularul de login s-a schimbat sau cookie-urile au fost respinse |
| `Formularul de login B2C s-a schimbat` | Structură nouă a paginii de login |
| `/api/...: HTTP 5xx` | Eroare temporară pe serverul Premier Energy |

### „Login-ul a cerut un pas suplimentar”

Premier Energy cere o acțiune în browser: MFA, schimbarea parolei sau acceptarea termenilor. Autentifică-te o dată pe app.premierenergy.ro, finalizează pasul și reîncarcă integrarea.

### Senzorii arată „Indisponibil”

- Uită-te în log după `UpdateFailed`
- Apasă butonul **Actualizare date**
- Dacă problema persistă după mai multe intervale, verifică portalul în browser

### „Consum ultima lună” sau „Ultima plată” sunt goale

Structura acestor răspunsuri poate diferi între conturi. Descarcă diagnosticul și verifică `structura_raspunsuri`:

- `consum_exemplu` trebuie să conțină `contracte` → `consum` → `dataCitire`, `consumMWH`
- `recentPayments_tip` arată tipul răspunsului de plăți

Trimite aceste chei (nu valorile) într-un issue ca să poată fi adaptat parserul.

### Perioada de transmitere index arată „Perioadă indisponibilă”

Portalul nu a trimis `perioada_citire_start` / `perioada_citire_sfarsit` pentru acel loc de consum. Se întâmplă, de exemplu, la contoarele citite de distribuitor (fără autocitire).

### Serviciul `trimite_index` dă eroare

- Verifică dacă **Transmitere index permisă** este `on`
- Indexul trebuie să fie un număr întreg, mai mare decât indexul anterior
- Mesajul exact de la Premier Energy apare în eroare și în log

---

## Log-uri utile de referință

### Login reușit

```
DEBUG (MainThread) [custom_components.premierenergy.api] Autentificare Premier Energy reușită
```

### Refresh token expirat (normal, la ~24h)

```
DEBUG (MainThread) [custom_components.premierenergy.api] Refresh token eșuat (...), reautentificare
DEBUG (MainThread) [custom_components.premierenergy.api] Autentificare Premier Energy reușită
```

### Endpoint opțional indisponibil (nu blochează restul datelor)

```
DEBUG (MainThread) [custom_components.premierenergy.coordinator] soldNeasociat indisponibil: ...
DEBUG (MainThread) [custom_components.premierenergy.coordinator] recentPayments indisponibil pentru RO005E...: ...
```

---

## Contactare suport

Deschide un issue cu:

1. Versiunea Home Assistant și a integrării
2. Log-urile de debug (fără parolă sau date personale)
3. Diagnosticul descărcat
4. Pașii prin care se reproduce problema
