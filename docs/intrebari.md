# ❓ Întrebări

[← Înapoi la README](../README.md)

**Teme:** [🔐 Cont și siguranță](#-cont-și-siguranță) · [📊 Cifrele](#-cifrele) · [🔢 Indexul](#-indexul) · [🚧 Limite](#-limite)

---

## 🔐 Cont și siguranță

<details>
<summary><b>De ce cere integrarea parola, nu un token sau o cheie API?</b></summary>

Premier Energy nu oferă chei API pentru clienți. Aplicația lor web se autentifică prin Azure AD B2C, cu email și parolă, iar integrarea face exact același lucru. Sesiunea obținută expiră cam la 24 de ore. Ca să o poată reînnoi fără să te deranjeze, integrarea are nevoie de parolă.

</details>

<details>
<summary><b>Unde rămâne parola? Pleacă undeva?</b></summary>

Rămâne în configurația locală Home Assistant (`.storage/core.config_entries`), la fel ca la orice integrare cu utilizator și parolă. Singurele adrese contactate sunt `login.premierenergy.ro` și `app.premierenergy.ro`. Nu există servere intermediare, telemetrie sau licențe care să verifice ceva online.

</details>

<details>
<summary><b>Poate integrarea să modifice ceva în contul meu?</b></summary>

Doar dacă apelezi tu acțiunea `premierenergy.trimite_index`. În rest, integrarea doar citește date.

</details>

<details>
<summary><b>Ce se vede din datele mele în diagnostic?</b></summary>

În diagnostic apar cifrele (consum, sume, numere de facturi) și numele câmpurilor primite de la API. Sunt mascate:
- adresa
- emailul
- POD-ul
- partenerul
- numerele de contract

Poți atașa fișierul la un issue fără grijă, dar verifică-l oricum înainte.

</details>

<details>
<summary><b>Am două conturi Premier Energy, de exemplu casă și apartament pe nume diferite. Merge?</b></summary>

Da. Adaugă integrarea de două ori, câte o dată pentru fiecare email. Dacă ai mai multe locuri de consum pe același cont, adaugi contul o singură dată și alegi locurile de consum din listă.

</details>

---

## 📊 Cifrele

<details>
<summary><b>„Total de plată” nu e egal cu suma facturilor neplătite. De ce?</b></summary>

Totalul include și **soldul neasociat**: bani plătiți care nu au fost încă alocați pe o factură, de obicei un avans sau o plată făcută cu alt cod. Aplicația Premier Energy calculează totalul la fel. Cele două componente apar separat în atributele `rest_facturi` și `sold_neasociat`.

</details>

<details>
<summary><b>Ce înseamnă „Stornată” și „Storno”? De ce nu le văd în liste?</b></summary>

- O factură **stornată** a fost anulată.
- Documentul **storno** e cel prin care a fost anulată.

Cele două se anulează reciproc, așa că integrarea nu le include în listele de facturi plătite sau neplătite și nici în „Ultima factură”. Aplicația web le afișează gri, din același motiv.

</details>

<details>
<summary><b>Luna din „Consum ultima lună” pare decalată.</b></summary>

Eticheta lunii vine din **data citirii** perioadei. Dacă distribuitorul citește contorul pe 1 noiembrie pentru consumul din octombrie, perioada apare ca „noiembrie”. Pentru intervalul exact, verifică atributele `de_la` și `pana_la`.

</details>

<details>
<summary><b>Pot pune consumul în Energy Dashboard?</b></summary>

Nu în mod util. Energy Dashboard are nevoie de un contor care crește continuu, cu valori măcar orare. Premier Energy oferă doar totaluri lunare. Pentru grafic, folosește istoricul din dashboard sau cardul ApexCharts ([instalare.md](instalare.md#4-pune-dashboard-ul)).

</details>

<details>
<summary><b>Cât de repede văd o factură nouă sau o plată?</b></summary>

Cel târziu după un interval de actualizare (implicit 6 ore), plus timpul în care Premier Energy procesează plata. Dacă vrei să verifici imediat, apasă **Actualizare date**.

</details>

<details>
<summary><b>Pot descărca PDF-ul facturii din Home Assistant?</b></summary>

Încă nu. Atributul `pdf` îți spune dacă factura are PDF în portal. Codul are deja funcția de descărcare, așa că o entitate sau o acțiune pentru PDF e o extensie posibilă.

</details>

---

## 🔢 Indexul

<details>
<summary><b>De ce „Perioadă transmitere index” arată „Perioadă indisponibilă”?</b></summary>

Portalul nu a trimis datele ferestrei de autocitire pentru acel loc de consum. Se întâmplă mai ales când contorul e citit de distribuitor sau e un contor inteligent, adică atunci când nu ai de transmis index.

</details>

<details>
<summary><b>Pot trimite indexul în afara ferestrei?</b></summary>

Acțiunea va încerca, dar Premier Energy respinge de obicei cererea, iar mesajul lor apare în eroare. Integrarea scrie și un avertisment în log. Folosește senzorul binar **Transmitere index permisă** ca o condiție în scripturi.

</details>

<details>
<summary><b>Ce contract folosește acțiunea de trimitere a indexului?</b></summary>

Folosește **contractul de furnizare** al locului de consum, la fel ca aplicația web. Dacă acesta lipsește, folosește contul contract. Tu dai doar POD-ul și valoarea.

</details>

---

## 🚧 Limite

<details>
<summary><b>Am pornit autentificarea în doi pași. Integrarea mai merge?</b></summary>

Nu. Login-ul automat funcționează doar cu email și parolă. Dacă Premier Energy cere un pas în plus, integrarea se oprește și îți spune că portalul a cerut o acțiune în browser.

</details>

<details>
<summary><b>Ce se întâmplă dacă Premier Energy schimbă aplicația?</b></summary>

Integrarea folosește aceleași adrese ca aplicația lor web. Dacă acestea se schimbă, senzorii devin *Indisponibil* și în log apar mesaje clare (vezi [depanare.md](depanare.md#ce-înseamnă-mesajele-din-log)). Problema se rezolvă cu o versiune nouă a integrării.

</details>

<details>
<summary><b>E o integrare oficială?</b></summary>

Nu. E un proiect personal, publicat cu licență MIT, fără nicio legătură cu Premier Energy.

</details>
