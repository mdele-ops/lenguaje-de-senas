"""Segunda rejilla: mas altura en Thumb1.z y curva en Thumb2.z, buscando el arco de la C."""
import itertools
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from playwright.sync_api import sync_playwright

import c_lab
import lab
import pulgar_c  # parchea lab.URL y lab.BONES
from pulgar_c4 import POSE_C, extra_metrics, variante

OBJ_ABERTURA = 0.62
OBJ_DY = 0.38
OBJ_ARRIBA = 0.55


def main():
    catalog = lab.load_catalog()
    filas = []
    rejilla = list(
        itertools.product(
            (0.2, 0.35, 0.5),    # tcurl
            (0.3, 0.6),          # taside
            (25, 40),            # Thumb1.y
            (35, 50, 65, 80),    # Thumb1.z
            (0, 20, 40),         # Thumb2.z
        )
    )
    print("casos:", len(rejilla), flush=True)
    with sync_playwright() as p:
        browser = c_lab.launch(p)
        page = lab.open_lab(browser, catalog)
        unit = c_lab.scales(page)
        for tcurl, taside, y, z, t2z in rejilla:
            lab.apply_pose(page, variante(tcurl, taside, y, z, t2z))
            m = c_lab.metrics(page, unit)
            m.update(extra_metrics(page, unit))
            m["caso"] = f"c{tcurl}_a{taside}_y{y}_z{z}_t2z{t2z}"
            m["params"] = (tcurl, taside, y, z, t2z)
            m["obj"] = round(
                abs(m["abertura"] - OBJ_ABERTURA) * 2.5
                + abs(m["dy"] - OBJ_DY) * 2.0
                + abs(m["arriba"] - OBJ_ARRIBA) * 2.5,
                4,
            )
            filas.append(m)
        browser.close()
    filas.sort(key=lambda r: r["obj"])
    for r in filas[:20]:
        print(
            f"{r['caso']:30s} obj={r['obj']:.3f} abertura={r['abertura']:.3f} "
            f"dy={r['dy']:+.3f} arriba={r['arriba']:+.3f} curva={r['curva']:.3f}"
        )
    Path("screenshots/pulgar_c6.json").write_text(
        json.dumps(filas, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
