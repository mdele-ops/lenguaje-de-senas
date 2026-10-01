"""Rejilla del pulgar de la C: mide sin fotografiar y ordena por cercania al objetivo."""
import itertools
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from playwright.sync_api import sync_playwright

import c_lab
import lab
import pulgar_c  # parchea lab.URL y lab.BONES

BASE = json.loads(
    (Path(__file__).resolve().parents[1] / "data" / "catalogo-lsm.json").read_text(
        encoding="utf-8"
    )
)
POSE_C = next(s for s in BASE["senas"] if s["letra"] == "C")["pose"]

# Objetivo leido de la foto de referencia: hueco claro y punta del pulgar algo
# mas abajo que la del indice, con el pulgar apuntando hacia arriba.
OBJ_ABERTURA = 0.62
OBJ_DY = 0.42
OBJ_ARRIBA = 0.45


def variante(tcurl, taside, y, z, t2z=0):
    pose = json.loads(json.dumps(POSE_C))
    pose["thumb"] = {"curl": tcurl, "aside": taside}
    pose["extra"]["RightHandThumb1"] = {"y": y, "z": z}
    if t2z:
        pose["extra"]["RightHandThumb2"] = {"z": t2z}
    return pose


def extra_metrics(page, unit):
    v = lab.vectors(page, side="right")
    o = lab.orientation(v, side="right")
    eje = lab.norm(lab.sub(v["thumbTip"], v["thumb1"]))
    return {
        # 1 = pulgar apuntando en la misma direccion que los dedos (hacia arriba)
        "arriba": round(c_lab.dot(eje, o["dedos"]), 3),
        # cuerda del pulgar: 1 = estirado, menos = curvado
        "curva": round(
            lab.length(lab.sub(v["thumb1"], v["thumbTip"])) / unit["pulgar"], 3
        ),
    }


def main():
    catalog = lab.load_catalog()
    filas = []
    rejilla = list(
        itertools.product(
            (0.25, 0.4, 0.55),      # tcurl
            (0.2, 0.45, 0.7),       # taside
            (10, 25, 40),           # Thumb1.y
            (35, 45, 55, 65),       # Thumb1.z
        )
    )
    print("casos:", len(rejilla), flush=True)
    with sync_playwright() as p:
        browser = c_lab.launch(p)
        page = lab.open_lab(browser, catalog)
        unit = c_lab.scales(page)
        for tcurl, taside, y, z in rejilla:
            pose = variante(tcurl, taside, y, z)
            lab.apply_pose(page, pose)
            m = c_lab.metrics(page, unit)
            m.update(extra_metrics(page, unit))
            m["caso"] = f"c{tcurl}_a{taside}_y{y}_z{z}"
            m["params"] = (tcurl, taside, y, z)
            m["obj"] = round(
                abs(m["abertura"] - OBJ_ABERTURA) * 2.5
                + abs(m["dy"] - OBJ_DY) * 2.0
                + abs(m["arriba"] - OBJ_ARRIBA) * 1.5,
                4,
            )
            filas.append(m)
        browser.close()
    filas.sort(key=lambda r: r["obj"])
    for r in filas[:18]:
        print(
            f"{r['caso']:26s} obj={r['obj']:.3f} abertura={r['abertura']:.3f} "
            f"dy={r['dy']:+.3f} arriba={r['arriba']:+.3f} curva={r['curva']:.3f}"
        )
    Path("screenshots/pulgar_c4.json").parent.mkdir(exist_ok=True)
    Path("screenshots/pulgar_c4.json").write_text(
        json.dumps(filas, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
