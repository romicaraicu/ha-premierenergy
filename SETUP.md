# SETUP: ghid complet de instalare și configurare

Ghidul te duce pas cu pas de la zero până la o integrare Premier Energy funcțională, cu dashboard.

---

## Cerințe preliminare

- Home Assistant **2024.12** sau mai nou (Core, OS, Supervised sau Container)
- Un cont activ pe [app.premierenergy.ro](https://app.premierenergy.ro/), cu email și parolă
- Contul trebuie să aibă cel puțin un loc de consum asociat
- Recomandat: [HACS](https://hacs.xyz/) instalat

> **Verifică întâi contul.** Autentifică-te o dată pe app.premierenergy.ro din browser. Dacă portalul îți cere să accepți termeni noi sau să schimbi parola, fă asta înainte de a configura integrarea.

---

## Instalare prin HACS (recomandat)

1. Încarcă acest proiect într-un repository GitHub (public sau privat, accesibil HACS-ului)
2. În Home Assistant, deschide **HACS**
3. Apasă ⋮ (dreapta sus) și alege **Custom repositories**
4. Lipește URL-ul repository-ului și alege categoria **Integration**
5. Caută **Premier Energy** în HACS și apasă **Download**
6. Restartează Home Assistant: **Setări** → **Sistem** → ⏻ → **Repornește Home Assistant**

---

## Instalare manuală

1. Accesează directorul de configurare Home Assistant (`/config`) prin Samba, SSH, add-on-ul *File editor* sau *Studio Code Server*
2. Dacă nu există, creează directorul `custom_components`
3. Copiază folderul `custom_components/premierenergy` din acest proiect, ca structura să arate așa:

```
config/
└── custom_components/
    └── premierenergy/
        ├── __init__.py
        ├── api.py
        ├── manifest.json
        └── ...
```

4. Restartează Home Assistant

---

## (Opțional) Testează conexiunea înainte de instalare

Din folderul proiectului, pe orice calculator cu Python 3.11+:

```bash
python3 -m venv .venv
```

```bash
.venv/bin/pip install aiohttp
```

```bash
.venv/bin/python tools/test_connection.py
```

Scriptul cere emailul și parola, se autentifică și afișează:

- **structura** răspunsurilor API (doar chei și tipuri, fără valori personale)
- **ce va vedea Home Assistant** pentru fiecare loc de consum (consum, facturi, total de plată, perioada de index)

Dacă aici apare `✓ Autentificat` și datele arată corect, integrarea va funcționa la fel și în Home Assistant.

---

## Configurare inițială

### Pasul 1: adaugă integrarea

1. **Setări** → **Dispozitive și servicii** → **+ Adaugă integrare**
2. Caută **Premier Energy**
3. Introdu **emailul** și **parola** contului app.premierenergy.ro
4. Apasă **Trimite**

Integrarea se autentifică și descarcă lista locurilor de consum.

### Pasul 2: alege locurile de consum

Dacă ai mai multe locuri de consum, apare o listă din care le alegi pe cele de monitorizat. Tot aici setezi intervalul de actualizare (implicit **6 ore**).

Dacă ai un singur loc de consum, pasul este sărit automat.

### Pasul 3: verifică entitățile

Mergi la **Setări** → **Dispozitive și servicii** → **Premier Energy**. Pentru fiecare loc de consum vei vedea un dispozitiv cu 12 senzori, 2 senzori binari și un buton. Lista completă e în [README.md](README.md#entități-create).

---

## Instalare dashboard

1. Află POD-ul: deschide dispozitivul Premier Energy. Codul apare ca număr de serie și în atributul `pod` al senzorului „Loc de consum”.
2. Generează fișierul dashboard:

```bash
python3 tools/genereaza_dashboard.py RO005E123456789
```

3. În Home Assistant: **Setări** → **Panouri de bord** → **+ Adaugă panou** → **Pornește de la zero**, cu numele „Premier Energy” și iconița `mdi:lightning-bolt-circle`
4. Deschide panoul nou, apasă ✏️ (Editează) → ⋮ → **Editor de configurație brută**
5. Șterge tot conținutul, lipește conținutul din `dashboard/premierenergy_RO005E123456789.yaml` și apasă **Salvează**

**Grafic opțional:** instalează `apexcharts-card` din HACS (secțiunea *Frontend*). Apoi adaugă un card **Manual** cu conținutul din `dashboard/card_grafic_consum_RO005E123456789.yaml`.

---

## Reconfigurare

**Setări** → **Dispozitive și servicii** → **Premier Energy** → **Configurare** (⚙️):

- **Locuri de consum**: adaugă sau elimină POD-uri
- **Interval de actualizare**: între 1 și 24 de ore

Integrarea se reîncarcă automat.

### Schimbare parolă

Dacă îți schimbi parola pe portal, Home Assistant afișează notificarea **„Reautentificare necesară”**. Apasă pe ea și introdu parola nouă.

---

## Interval de actualizare

| Interval | Când e potrivit |
|----------|-----------------|
| 1–3 ore | Vrei să vezi rapid o factură nouă sau confirmarea plății |
| **6 ore** (implicit) | Echilibru bun; facturile și consumul se schimbă oricum lunar |
| 12–24 ore | Minim de cereri către portal |

Poți forța oricând o actualizare cu butonul **Actualizare date**.

---

## Erori posibile la configurare

| Eroare | Cauză | Soluție |
|--------|-------|---------|
| „Email sau parolă incorecte” | Credențiale greșite | Verifică-le pe app.premierenergy.ro |
| „Nu mă pot conecta la Premier Energy” | Portal indisponibil, rețea sau login schimbat | Încearcă mai târziu; vezi [DEBUG.md](DEBUG.md) |
| „Contul nu are niciun loc de consum asociat” | Contul nu are contracte active | Asociază locul de consum din portal |
| „Acest cont este deja configurat” | Emailul e deja adăugat | Folosește **Configurare** pe intrarea existentă |

---

## Dezinstalare

1. **Setări** → **Dispozitive și servicii** → **Premier Energy** → ⋮ → **Șterge**
2. Dacă ai instalat prin HACS: HACS → Premier Energy → ⋮ → **Remove**
3. Dacă ai instalat manual: șterge `config/custom_components/premierenergy`
4. Restartează Home Assistant
