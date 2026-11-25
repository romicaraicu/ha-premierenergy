# Istoric versiuni

Versiunile urmează [SemVer](https://semver.org/lang/ro/):
- **0.x.0**: funcții noi (senzori, carduri, acțiuni)
- **0.x.y**: reparații și documentație

Pașii de actualizare sunt în [docs/actualizare.md](docs/actualizare.md).

---

## 0.2.0 · 2026-11-25

**Nou**
- Senzor **Plătit în anul curent** (`sensor.premierenergy_<pod>_cost_an_curent`). Atributul `cost_anual` conține, pentru fiecare an: suma plătită, suma facturată, restul de plată, numărul de facturi, kWh consumați și prețul mediu pe kWh.
- Dashboard: secțiune nouă **Cost pe ani**, cu tabel și bare.

**De făcut după actualizare**
- Ca să apară secțiunea nouă, regenerează dashboard-ul și lipește-l din nou (vezi [ghidul de actualizare](https://github.com/romicaraicu/ha-premierenergy/blob/main/docs/actualizare.md#2-actualizează-dashboard-ul)).

## 0.1.1 · 2026-11-24

- Documentație rescrisă: README nou și ghiduri în `docs/`
- Instalare prin Marketplace (Home Assistant 2026.11+)
- `.gitignore` exclude dashboard-urile generate (conțin POD-ul)

## 0.1.0 · 2026-11-24

Prima versiune:
- login cu email și parolă
- locuri de consum, consum lunar, facturi de plată și plătite, plăți
- perioada de transmitere a indexului
- acțiunea `premierenergy.trimite_index`
- dashboard
