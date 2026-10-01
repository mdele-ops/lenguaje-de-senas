"""Rejilla del pulgar de la C sobre los ejes que si lo levantan (Thumb1.z y Thumb2.x).

El diagnostico de pulgar_c11 dejo claro que Thumb1.z sube la punta y cierra el
hueco, y que Thumb2.x negativo la sube ademas de orientarla hacia los dedos.
Aqui se combinan con el curl y el aside para acercarse a la foto de referencia.
"""
import itertools
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from playwright.sync_api import sync_playwright

import c_lab
import lab
import pulgar_c  # parchea lab.URL y lab.BONES
from pulgar_c4 import POSE_C, extra_metrics

OUT = Path(__file__).resolve().parent / "screenshots" / "pulgar_c12"

# Objetivo leido de la foto: hueco visible pero cerrado, punta del pulgar bien
# por debajo del indice y apuntando hacia arriba (misma direccion que los dedos).
OBJ_ABERTURA = 0.62
OBJ_DY = 0.40
OBJ_ARRIBA = 0.50


def variante(tcurl, taside, t1x, t1z, t2x):
    pose = json.loads(json.dumps(POSE_C))
    pose["thumb"] = {"curl": tcurl, "aside": taside}
    t1 = {"y": 34, "z": t1z}
    if t1x:
        t1["x"] = t1x
    pose["extra"]["RightHandThumb1"] = t1
    if t2x:
        pose["extra"]["RightHandThumb2"] = {"x": t2x}
    else:
        pose["extra"].pop("RightHandThumb2", None)
    return pose


def main():
    catalog = lab.load_catalog()
    OUT.mkdir(parents=True, exist_ok=True)
    rejilla = list(
        itertools.product(
            (0.42, 0.55, 0.70),   # tcurl
            (0.5, 0.8),           # taside
            (-30, -15, 0),        # Thumb1.x
            (8, 25, 40, 55),      # Thumb1.z
            (-30, -15, 0),        # Thumb2.x
        )
    )
    print("casos:", len(rejilla), flush=True)
    filas = []
    with sync_playwright() as p:
        browser = c_lab.launch(p)
        page = lab.open_lab(browser, catalog)
        unit = c_lab.scales(page)
        for params in rejilla:
            lab.apply_pose(page, variante(*params))
            m = c_lab.metrics(page, unit)
            m.update(extra_metrics(page, unit))
            m["params"] = params
            m["caso"] = "c{0}_a{1}_x{2}_z{3}_t2x{4}".format(*params)
            m["obj"] = round(
                abs(m["abertura"] - OBJ_ABERTURA) * 2.5
                + abs(m["dy"] - OBJ_DY) * 2.0
                + abs(m["arriba"] - OBJ_ARRIBA) * 2.0,
                4,
            )
            filas.append(m)
        browser.close()
    filas.sort(key=lambda r: r["obj"])
    for r in filas[:20]:
        print(
            f"{r['caso']:28s} obj={r['obj']:.3f} abertura={r['abertura']:.3f} "
            f"dy={r['dy']:+.3f} arriba={r['arriba']:+.3f} curva={r['curva']:.3f}",
            flush=True,
        )
    (OUT / "metricas.json").write_text(
        json.dumps(filas, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
