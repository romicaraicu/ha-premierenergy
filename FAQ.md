# FAQ: întrebări frecvente

---

### Ce credențiale folosesc?

Aceleași email și parolă cu care intri pe [app.premierenergy.ro](https://app.premierenergy.ro/). Nu e nevoie de chei API sau alte coduri.

### Unde sunt salvate emailul și parola?

În configurația Home Assistant (`.storage/core.config_entries`), ca la orice altă integrare. Parola e necesară pentru login-ul automat după expirarea sesiunii. Nu e trimisă nicăieri altundeva decât la `login.premierenergy.ro`.

### Ce date extrage integrarea din contul meu?

Locurile de consum, facturile, consumul lunar, plățile recente, soldul neasociat și perioada de transmitere a indexului. Nu modifică nimic în cont, cu excepția situației în care apelezi explicit serviciul `premierenergy.trimite_index`.

### Ce este un POD?

POD (Point of Delivery) este codul unic al locului de consum, de forma `RO005E…`. Îl găsești pe factură și în aplicația Premier Energy.

### Cât de des se actualizează datele?

Implicit la fiecare 6 ore. Poți schimba intervalul între 1 și 24 de ore din **Configurare**. Butonul **Actualizare date** forțează o citire imediată.

### Pot adăuga mai multe conturi Premier Energy?

Da. Adaugă integrarea de mai multe ori, câte o dată pentru fiecare email.

### Pot alege ce locuri de consum să monitorizez?

Da, la configurare sau ulterior din **Configurare** → **Locuri de consum**.

### Cum se calculează „Total de plată”?

La fel ca în aplicația web: suma resturilor de plată ale facturilor plus soldul neasociat al locului de consum. O valoare negativă înseamnă că ai credit sau avans.

### Ce înseamnă statusurile facturilor?

| Status | Semnificație |
|--------|--------------|
| Plătită | Rest de plată 0 |
| Parțial plătită | S-a plătit o parte din valoare |
| Neplătită | Nimic plătit |
| În procesare | Portalul nu a raportat încă restul de plată |
| Stornată / Storno | Factură anulată, respectiv documentul de anulare (nu apar în liste) |

O factură e **restantă** dacă are rest de plată și scadența a trecut.

### De ce „Consum ultima lună” nu apare în Energy Dashboard?

Portalul raportează consumul lunar, pe facturi, nu un index care crește continuu. Energy Dashboard are nevoie de senzori `total_increasing`, cu date cel puțin orare. Pentru grafice folosește dashboard-ul inclus sau cardul ApexCharts.

### Cum transmit indexul din Home Assistant?

Cu serviciul `premierenergy.trimite_index` (POD + index), doar în perioada de transmitere. README conține un exemplu complet, cu helper și script pentru dashboard.

### De unde știu când pot transmite indexul?

Senzorul binar **Transmitere index permisă** este `on` în perioada de autocitire. Senzorul **Perioadă transmitere index** arată intervalul, iar în atribute găsești câte zile au rămas. README are și o automatizare care te anunță când se deschide perioada.

### Pot descărca PDF-ul facturii?

Clientul API suportă descărcarea (`get_invoice_pdf`), dar momentan integrarea nu expune o entitate pentru PDF. Atributul `pdf` arată dacă factura are PDF disponibil în portal.

### De ce am primit „Reautentificare necesară”?

Portalul a refuzat emailul sau parola, de obicei pentru că ai schimbat parola. Apasă pe notificare și introdu parola nouă.

### Funcționează dacă am autentificare în doi pași (MFA)?

Nu. Login-ul automat funcționează doar cu email și parolă.

### Integrarea e oficială?

Nu. Este o integrare comunitară, neafiliată cu Premier Energy, care folosește același API ca aplicația web oficială.

### Integrarea trimite date personale către terți?

Nu. Comunică doar cu `login.premierenergy.ro` și `app.premierenergy.ro`. Diagnosticul descărcabil maschează adresa, emailul și numerele de contract.

### Cum raportez o problemă?

Activează log-urile de debug și descarcă diagnosticul (vezi [DEBUG.md](DEBUG.md)), apoi deschide un issue. Nu publica parola, adresa sau codul POD.
