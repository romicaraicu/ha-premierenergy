# 🧪 Rețete

[← Înapoi la README](../README.md)

Bucăți de configurație gata de copiat. În toate, înlocuiește:
- `ro005e123456789` cu POD-ul tău, cu litere mici (în ID-uri de entități)
- `RO005E123456789` cu POD-ul tău, cu majuscule (în acțiunea de transmitere index)
- `notify.mobile_app_telefon` cu serviciul tău de notificare

Le poți lipi în `automations.yaml` / `scripts.yaml` sau în editorul de automatizări, în modul YAML.

- [Te anunță când se deschide fereastra de index](#fereastra-de-index-s-a-deschis)
- [Ultima zi pentru index](#ultima-zi-pentru-index)
- [Factură nouă](#factură-nouă)
- [Scadență peste 3 zile](#scadență-peste-3-zile)
- [Factură restantă](#factură-restantă)
- [Trimite indexul din dashboard](#trimite-indexul-din-dashboard)
- [Template-uri utile](#template-uri-utile)

---

## Fereastra de index s-a deschis

```yaml
alias: Premier Energy · poți trimite indexul
triggers:
  - trigger: state
    entity_id: binary_sensor.premierenergy_ro005e123456789_perioada_index_activa
    from: "off"
    to: "on"
actions:
  - action: notify.mobile_app_telefon
    data:
      title: ⚡ Index Premier Energy
      message: >
        Fereastra e deschisă până pe
        {{ states('sensor.premierenergy_ro005e123456789_perioada_index_sfarsit') }}.
```

## Ultima zi pentru index

O reamintire la 18:00, în ultima zi a ferestrei, dacă portalul nu raportează că ai transmis deja:

```yaml
alias: Premier Energy · ultima zi pentru index
triggers:
  - trigger: time
    at: "18:00:00"
conditions:
  - condition: state
    entity_id: binary_sensor.premierenergy_ro005e123456789_perioada_index_activa
    state: "on"
  - condition: template
    value_template: >
      {{ states('sensor.premierenergy_ro005e123456789_perioada_index_sfarsit') == now().date() | string
         and not state_attr('sensor.premierenergy_ro005e123456789_perioada_index', 'index_transmis') }}
actions:
  - action: notify.mobile_app_telefon
    data:
      message: Azi e ultima zi în care poți trimite indexul la Premier Energy.
```

## Factură nouă

Se declanșează când se schimbă numărul celei mai recente facturi:

```yaml
alias: Premier Energy · factură nouă
triggers:
  - trigger: state
    entity_id: sensor.premierenergy_ro005e123456789_ultima_factura
    attribute: numar
conditions:
  - "{{ trigger.from_state is not none and trigger.from_state.attributes.numar is defined }}"
actions:
  - action: notify.mobile_app_telefon
    data:
      title: 🧾 Factură nouă
      message: >
        {% set f = trigger.to_state.attributes %}
        Nr. {{ f.numar }}: {{ '%.2f' | format(f.valoare) }} lei, scadentă pe
        {{ (f.scadenta | as_datetime).strftime('%d.%m.%Y') }}.
```

## Scadență peste 3 zile

```yaml
alias: Premier Energy · scadență apropiată
triggers:
  - trigger: time
    at: "09:00:00"
conditions:
  - condition: template
    value_template: >
      {% set s = states('sensor.premierenergy_ro005e123456789_urmatoarea_scadenta') %}
      {{ s not in ['unknown', 'unavailable']
         and (as_datetime(s).date() - now().date()).days == 3 }}
actions:
  - action: notify.mobile_app_telefon
    data:
      message: >
        Peste 3 zile ai de plată
        {{ states('sensor.premierenergy_ro005e123456789_total_de_plata') }} lei la Premier Energy.
```

## Factură restantă

```yaml
alias: Premier Energy · restanță
triggers:
  - trigger: state
    entity_id: binary_sensor.premierenergy_ro005e123456789_factura_restanta
    to: "on"
actions:
  - action: persistent_notification.create
    data:
      title: Premier Energy
      message: >
        Ai {{ state_attr('binary_sensor.premierenergy_ro005e123456789_factura_restanta', 'restant') }}
        lei trecuți de scadență.
```

---

## Trimite indexul din dashboard

Ai nevoie de trei lucruri: un câmp numeric, un script și cardul (deja pregătit, dar comentat) din dashboard.

**1. Câmpul numeric.** Îl poți crea din **Setări** → **Dispozitive și servicii** → **Ajutoare** → **Număr**, cu ID-ul `input_number.premierenergy_index`. Sau în YAML:

```yaml
input_number:
  premierenergy_index:
    name: Index contor
    min: 0
    max: 9999999
    step: 1
    mode: box
```

**2. Scriptul** (`scripts.yaml`):

```yaml
premierenergy_trimite_index:
  alias: Premier Energy · trimite index
  icon: mdi:send
  sequence:
    # oprește scriptul dacă helper-ul lipsește sau indexul e 0
    - condition: template
      value_template: "{{ states('input_number.premierenergy_index') | int(0) > 0 }}"
    - action: premierenergy.trimite_index
      data:
        pod: RO005E123456789
        index: "{{ states('input_number.premierenergy_index') | int(0) }}"
      response_variable: raspuns
    - action: persistent_notification.create
      data:
        title: Premier Energy
        message: "{{ raspuns.mesaj }}"
```

**3. Cardul.** În dashboard, la secțiunea *Transmitere index*, scoate `#` din fața blocului `type: entities`. Cardul apare doar cât timp fereastra e deschisă și cere confirmare înainte să trimită.

---

## Template-uri utile

```jinja
{# Lei de plată, ca număr #}
{{ states('sensor.premierenergy_ro005e123456789_total_de_plata') | float(0) }}

{# Câte zile mai ai pentru index #}
{{ state_attr('sensor.premierenergy_ro005e123456789_perioada_index', 'zile_ramase') }}

{# Consumul mediu lunar din ultimele 12 perioade #}
{% set h = (state_attr('sensor.premierenergy_ro005e123456789_consum_ultima_luna', 'istoric') or [])[:12] %}
{{ (h | map(attribute='kwh') | sum / (h | count)) | round(0) if h else 0 }} kWh

{# Lista facturilor de plată, pe un rând #}
{% for f in state_attr('sensor.premierenergy_ro005e123456789_facturi_neplatite', 'facturi') or [] %}
{{ f.numar }} ({{ f.rest_plata }} lei){{ ', ' if not loop.last }}
{%- endfor %}
```
