# 🔄 Actualizare

[← Înapoi la README](../README.md)

Ghidul are două părți:

- **[A. Actualizează în Home Assistant](#a-actualizează-în-home-assistant)**: pentru oricine folosește integrarea
- **[B. Publică o versiune nouă](#b-publică-o-versiune-nouă)**: pentru cine întreține repository-ul (commit, tag, push, release)

Ce s-a schimbat în fiecare versiune găsești în [CHANGELOG.md](../CHANGELOG.md).

---

## A. Actualizează în Home Assistant

O actualizare are două părți independente:
- **integrarea** (codul și senzorii), care se actualizează din Marketplace
- **dashboard-ul**, pe care îl actualizezi tu

### 1. Actualizează integrarea

**Când apare singură.** Marketplace verifică repository-ul o dată la 48 de ore. Când găsește o versiune nouă, aceasta apare în **Setări** → **Actualizări** ca *Premier Energy x.y.z*. Apasă **Instalează**.

**Dacă nu vrei să aștepți.**
1. **Setări** → **Marketplace** → **Premier Energy**
2. ⋮ → **Install another version**
3. Alege versiunea nouă → **Install**

**După instalare:**
- dacă **Reparații** cere restart, acceptă-l
- verifică versiunea în **Setări** → **Dispozitive și servicii** → **Premier Energy**

Contul, locurile de consum și setările rămân la fel. Senzorii noi apar singuri pe dispozitiv. Cei existenți își păstrează ID-urile, așa că automatizările tale merg în continuare.

<details>
<summary>Ai instalat cu HACS sau manual?</summary>

- **HACS** (Home Assistant mai vechi de 2026.11): HACS → Premier Energy → **Update**, apoi restart.
- **Manual**: descarcă release-ul nou de pe GitHub, înlocuiește complet folderul `/config/custom_components/premierenergy`, apoi restart.

</details>

### 2. Actualizează dashboard-ul

Home Assistant nu actualizează un dashboard lipit în *Editorul de configurație brută*, așa că secțiunile noi trebuie aduse de mână. Ai două variante.

**Varianta 1: înlocuiești tot dashboard-ul.** E cea mai simplă, dar pierzi modificările făcute de tine în panou.

1. Pe calculator, adu ultima versiune a proiectului și generează din nou fișierul:
   ```bash
   cd ha-premierenergy
   ```
   ```bash
   git pull
   ```
   ```bash
   python3 tools/genereaza_dashboard.py RO005E123456789
   ```
2. În Home Assistant, deschide panoul **Premier Energy** → ✏️ → ⋮ → **Editor de configurație brută**.
3. Selectează tot textul și înlocuiește-l cu conținutul din `dashboard/premierenergy_<POD>.yaml`.
4. **Salvează**.

**Varianta 2: adaugi doar secțiunea nouă.** Îți păstrează modificările.

1. Generează fișierul ca la varianta 1.
2. În fișierul generat, caută comentariul cu numele secțiunii noi, de exemplu `COST PE ANI`, și copiază blocul care începe cu `- type: grid` de sub el.
3. În editorul brut al panoului, lipește blocul la sfârșitul listei `sections:`, cu aceeași indentare ca celelalte `- type: grid`.
4. **Salvează**.

> [!TIP]
> Înainte să modifici panoul, fă-ți o copie: în editorul brut, selectează tot și salvează textul într-un fișier. Dacă ceva nu arată bine, îl lipești înapoi.

### Nu văd senzorul nou

- Verifică dacă versiunea din **Dispozitive și servicii** e cea nouă. Dacă nu e, Home Assistant încă nu a repornit.
- Apasă butonul **Actualizare date** al dispozitivului.
- Dacă dashboard-ul arată *Entitate negăsită*, verifică dacă POD-ul din fișierul generat e cel corect.

---

## B. Publică o versiune nouă

Pașii de mai jos merg în terminal, pe Mac, din folderul proiectului. Merg la fel în zsh, bash și fish.

### Pasul 0: alege numărul versiunii

| Ce s-a schimbat | Exemplu | Versiune nouă |
|---|---|---|
| reparații, documentație | text corectat, un bug reparat | `0.2.0` → **`0.2.1`** |
| funcții noi | senzor nou, secțiune nouă în dashboard | `0.2.1` → **`0.3.0`** |
| schimbări care strică ceva la utilizatori | ID-uri de entități redenumite | `0.x` → **`1.0.0`** |

Mai jos, `0.2.0` ține locul versiunii tale.

### Pasul 1: pregătește fișierele

1. În `custom_components/premierenergy/manifest.json`, setează `"version": "0.2.0"`. Fără prefixul `v`.
2. În `CHANGELOG.md`, adaugă sus o secțiune `## 0.2.0 · AAAA-LL-ZZ` cu ce s-a schimbat. Din ea se construiesc și notele release-ului.

### Pasul 2: verifică înainte de commit

```bash
cd /Users/romicaraicu/OPS/ClaudeAI/mdk-claude/ha-premierenergy
```

Vezi ce s-a modificat:

```bash
git status --short
```

Te uiți după trei lucruri:
- **Nu** trebuie să apară fișiere cu POD-ul tău (`dashboard/premierenergy_DGS….yaml`), `.venv/` sau dump-uri JSON. Ele sunt în `.gitignore`, deci n-ar trebui să apară.
- `manifest.json` și `CHANGELOG.md` trebuie să fie în listă.
- Opțional, rulează testele, dacă ai mediul de test instalat: `python -m pytest -q`.

### Pasul 3: commit

```bash
git add -A
```

```bash
git commit -m "v0.2.0: cost pe ani"
```

Mesajul poate fi orice. Convenția din proiect e `vX.Y.Z: rezumat scurt`.

### Pasul 4: tag

Un tag este o etichetă pusă pe commit-ul exact care devine versiunea `v0.2.0`:

```bash
git tag -a v0.2.0 -m "v0.2.0"
```

Verifică dacă eticheta e pe ultimul commit:

```bash
git log --oneline --decorate -3
```

Trebuie să vezi `(HEAD -> main, tag: v0.2.0)` pe primul rând.

### Pasul 5: push

Trimite întâi commit-ul, apoi tag-ul:

```bash
git push
```

```bash
git push origin v0.2.0
```

### Pasul 6: release pe GitHub

Release-ul face versiunea vizibilă în Marketplace. Notele se iau din secțiunea versiunii din `CHANGELOG.md`:

```bash
awk '/^## 0.2.0/{f=1;next} /^## /{f=0} f' CHANGELOG.md > release-notes.md
```

```bash
gh release create v0.2.0 --verify-tag --title "v0.2.0" --notes-file release-notes.md
```

```bash
rm release-notes.md
```

`--verify-tag` oprește comanda dacă tag-ul nu e deja pe GitHub, adică dacă ai uitat pasul 5.

### Pasul 7: verifică

```bash
gh release list -R romicaraicu/ha-premierenergy
```

Versiunea nouă trebuie să fie **Latest**. De aici continui cu [partea A](#a-actualizează-în-home-assistant), în Home Assistant.

<details>
<summary><b>Am greșit ceva. Cum repar?</b></summary>

| Situație | Ce faci |
|---|---|
| Am uitat un fișier și **nu** am dat push | `git add <fișier>` și `git commit --amend --no-edit`, apoi mută tag-ul: `git tag -f -a v0.2.0 -m "v0.2.0"` |
| Am pus tag-ul pe commit-ul greșit, **înainte** de push | `git tag -d v0.2.0`, apoi creează-l din nou (pasul 4) |
| Am publicat deja release-ul și am găsit o greșeală | nu rescrie versiunea publicată; repar-o și publică `0.2.1` |
| `git push` cere utilizator și parolă | remote-ul e pe HTTPS: rulează `gh auth setup-git` sau trece pe SSH cu `git remote set-url origin git@github.com:romicaraicu/ha-premierenergy.git` |
| `gh release create` spune *tag not found* | ai sărit `git push origin v0.2.0` |

</details>
