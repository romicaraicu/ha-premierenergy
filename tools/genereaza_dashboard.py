#!/usr/bin/env python3
"""Generează dashboard-ul Premier Energy pentru un POD anume.

Utilizare:
    python3 tools/genereaza_dashboard.py RO005E123456789
    -> creează dashboard/premierenergy_RO005E123456789.yaml (gata de lipit)

Mai multe locuri de consum? Rulează scriptul o dată pentru fiecare POD.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLACEHOLDER = "ro005e000000000"


def slug(pod: str) -> str:
    """Aceeași transformare ca homeassistant.util.slugify pentru coduri POD."""
    return re.sub(r"[^a-z0-9]+", "_", pod.strip().lower()).strip("_")


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 1
    pod = sys.argv[1].strip()
    for name in ("premierenergy_dashboard.yaml", "card_grafic_consum_apexcharts.yaml"):
        src = ROOT / "dashboard" / name
        out = ROOT / "dashboard" / name.replace("premierenergy_dashboard", f"premierenergy_{pod}").replace(
            "card_grafic_consum_apexcharts", f"card_grafic_consum_{pod}"
        )
        out.write_text(src.read_text(encoding="utf-8").replace(PLACEHOLDER, slug(pod)), encoding="utf-8")
        print(f"✓ {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
