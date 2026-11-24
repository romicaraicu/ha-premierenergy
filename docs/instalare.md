# 📦 Instalare și configurare

[← Înapoi la README](../README.md)

Durează în jur de 10 minute. La final ai contul Premier Energy legat de Home Assistant și, dacă vrei, un panou dedicat cu toate datele.

**Cuprins**
1. [Înainte să începi](#1-înainte-să-începi)
2. [Alege cum instalezi](#2-alege-cum-instalezi)
3. [Leagă contul](#3-leagă-contul)
4. [Pune dashboard-ul](#4-pune-dashboard-ul)
5. [Mai târziu: opțiuni, parolă nouă, ștergere](#5-mai-târziu)

---

## 1. Înainte să începi

Bifează lista:

- [ ] Home Assistant **2024.12** sau mai nou (orice tip de instalare)
- [ ] Contul de pe [app.premierenergy.ro](https://app.premierenergy.ro/) merge în browser și vezi în el cel puțin un loc de consum
- [ ] Nu ai pași în așteptare pe portal: termeni noi de acceptat, schimbare de parolă impusă etc. Dacă ai, rezolvă-i întâi din browser.

<details>
<summary><b>Vrei să verifici contul înainte să instalezi ceva în Home Assistant?</b></summary>

Pe orice calculator cu Python 3.11+, din folderul proiectului:

```bash
python3 -m venv .venv
```
```bash
.venv/bin/pip install aiohttp
```
```bash
.venv/bin/python tools/test_connection.py
```

Scriptul cere emailul și parola, apoi afișează ce va vedea Home Assistant pentru fiecare loc de consum. Dacă vezi `✓ Autentificat` și cifrele seamănă cu cele din aplicație, poți trece mai departe.

</details>

---

## 2. Alege cum instalezi

| Versiunea Home Assistant | Metoda |
|---|---|
| 2026.11 sau mai nouă | **A. Marketplace** (recomandat) |
| mai veche de 2026.11 | **B. HACS** |
| orice versiune, fără magazin | **C. Copiere manuală** |

### A. Marketplace

Marketplace e inclus în Home Assistant de la 2026.11 și ia locul HACS. Acceptă orice repository public de pe GitHub care are un fișier `hacs.json`, iar acest proiect îl are.

1. Deschide **Setări** → **Marketplace**. Îl văd doar administratorii.
2. Apasă **Add from link** (dreapta sus).
3. Scrie `romicaraicu/ha-premierenergy` și apasă **Add**.
4. Prima dată, Marketplace cere legătura cu GitHub:
   - apasă **Continue**
   - deschide linkul și introdu codul afișat
   - aprobă accesul
5. Dacă te întreabă de **Type**, alege **Integration** și apasă din nou **Add**.
6. Deschide **Premier Energy** din listă, apasă **Install** și confirmă versiunea.
7. Dacă în **Reparații** apare o cerere de restart, accept-o.

Versiunile noi apar singure în **Setări** → **Actualizări**. Marketplace verifică repository-urile adăugate prin link o dată la două zile. Pentru o versiune anume: pagina integrării → ⋮ → **Install another version**.

### B. HACS

1. **HACS** → ⋮ → **Custom repositories**
2. Adaugă URL-ul `https://github.com/romicaraicu/ha-premierenergy`, cu tipul **Integration**
3. Caută *Premier Energy* → **Download**
4. Repornește Home Assistant

Când actualizezi Home Assistant la 2026.11, instalarea din HACS trece automat în Marketplace.

### C. Copiere manuală

Ai nevoie de acces la folderul `/config`, prin Samba, SSH sau unul dintre add-on-urile *File editor* / *Studio Code Server*. Copiază `custom_components/premierenergy` din acest repository, ca să obții:

```
/config/custom_components/premierenergy/manifest.json
/config/custom_components/premierenergy/__init__.py
…
```

Apoi repornește Home Assistant. La această metodă, actualizările le copiezi tot de mână.

---

## 3. Leagă contul

1. **Setări** → **Dispozitive și servicii** → **+ Adaugă integrare** → caută *Premier Energy*
2. Introdu **emailul** și **parola** de pe app.premierenergy.ro
3. Dacă ai **mai multe locuri de consum**, bifează-le pe cele care te interesează și alege la câte ore se citesc datele (implicit 6). Cu un singur loc de consum, ecranul ăsta nu mai apare.

Gata. Fiecare loc de consum devine un dispozitiv „Premier Energy *adresa*”, cu 12 senzori, 2 senzori binari și un buton. Ce înseamnă fiecare găsești în [entitati.md](entitati.md).

**Dacă formularul afișează o eroare:**

| Mesaj | Ce faci |
|---|---|
| *Email sau parolă incorecte.* | Încearcă aceleași date în browser; atenție la spațiile copiate la final |
| *Nu mă pot conecta la Premier Energy.* | Portalul sau rețeaua au o problemă; reîncearcă. Dacă persistă, vezi [depanare.md](depanare.md) |
| *Contul nu are niciun loc de consum asociat.* | Asociază locul de consum din aplicația Premier Energy |
| *Acest cont Premier Energy este deja configurat.* | Contul există deja; modifică-l din **Configurare** |

---

## 4. Pune dashboard-ul

Dashboard-ul din `dashboard/premierenergy_dashboard.yaml` folosește doar carduri incluse în Home Assistant. Conține patru zone:
- **Sumar** (total de plată, scadență, consum, ultima plată)
- **Transmitere index**
- **Facturi** (de plată și plătite)
- **Istoric consum**, cu bare

**Pas 1: află POD-ul.** Îl găsești pe dispozitiv, la numărul de serie, sau în atributul `pod` al senzorului *Loc de consum*.

**Pas 2: generează fișierul** pentru POD-ul tău:

```bash
python3 tools/genereaza_dashboard.py RO005E123456789
```

Scriptul creează `dashboard/premierenergy_<POD>.yaml`. Fișierul e exclus din git, pentru că conține POD-ul.

**Pas 3: creează panoul.**
1. **Setări** → **Panouri de bord** → **+ Adaugă panou** → **Pornește de la zero**. Pune-i titlul „Premier Energy” și iconița `mdi:lightning-bolt-circle`.
2. Deschide panoul → ✏️ → ⋮ → **Editor de configurație brută**.
3. Înlocuiește tot textul cu conținutul fișierului generat și salvează.

> [!TIP]
> **Grafic cu bare pentru consum.** Instalează cardul `apexcharts-card` din Marketplace (**Add from link** → `RomRider/apexcharts-card`) sau din HACS → *Frontend*. Apoi adaugă un card *Manual* cu conținutul lui `dashboard/card_grafic_consum_<POD>.yaml`.

Pentru un card care trimite indexul direct din dashboard, vezi [retete.md](retete.md#trimite-indexul-din-dashboard).

---

## 5. Mai târziu

**Alte POD-uri sau alt interval.** **Setări** → **Dispozitive și servicii** → **Premier Energy** → ⚙️ **Configurare**. După salvare, integrarea se reîncarcă singură.

**Cât de des să citească datele?** Facturile și consumul se schimbă o dată pe lună, deci nu are rost un interval foarte scurt:
- **1–3 h**: afli repede de o factură nouă sau de o plată confirmată
- **6 h** (implicit): suficient pentru aproape toată lumea
- **12–24 h**: cele mai puține cereri către Premier Energy

Pentru o citire imediată, apasă butonul **Actualizare date**.

**Ți-ai schimbat parola.** Home Assistant afișează *Reautentificare necesară*. Apasă pe notificare și introdu parola nouă; nu trebuie să ștergi nimic.

**Vrei să renunți.**
1. **Setări** → **Dispozitive și servicii** → **Premier Energy** → ⋮ → **Șterge**
2. Elimină și fișierele integrării, după cum ai instalat-o:
   - **Marketplace**: pagina integrării → ⋮ → **Uninstall**. Ca repository-ul să dispară și din listă, scoate-l din **Add from link**.
   - **HACS**: integrarea → ⋮ → **Remove**
   - **Manual**: șterge `/config/custom_components/premierenergy`
3. Repornește Home Assistant
