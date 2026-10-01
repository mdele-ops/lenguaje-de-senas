"""Diagnostico: que eje de RightHandThumb1/2 sube la punta del pulgar en la C.

Los barridos anteriores movieron solo Thumb1.z y la punta apenas subio. Aqui se
perturba un eje a la vez desde la pose guardada y se mide cuanto cambia la
altura de la punta, para saber sobre cual conviene trabajar.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from playwright.sync_api import sync_playwright

import c_lab
import lab
import pulgar_c  # parchea lab.URL y lab.BONES
from pulgar_c4 import POSE_C, extra_metrics

OUT = Path(__file__).resolve().parent / "screenshots" / "pulgar_c11"


def con_extra(**cambios):
    """POSE_C con los extras del pulgar reemplazados por `cambios`."""
    pose = json.loads(json.dumps(POSE_C))
    for hueso in ("RightHandThumb1", "RightHandThumb2", "RightHandThumb3"):
        pose["extra"].pop(hueso, None)
    for hueso, rot in cambios.items():
        pose["extra"][hueso] = rot
    return pose


def casos():
    base = POSE_C["extra"]["RightHandThumb1"]
    yield "guardada", json.loads(json.dumps(POSE_C))
    yield "sin_extra", con_extra()
    for eje in ("x", "y", "z"):
        for deg in (-40, -20, 20, 40):
            yield f"t1{eje}{deg:+03d}", con_extra(
                RightHandThumb1={**base, eje: base.get(eje, 0) + deg}
            )
    for eje in ("x", "y", "z"):
        for deg in (-30, 30):
            yield f"t2{eje}{deg:+03d}", con_extra(
                RightHandThumb1=dict(base), RightHandThumb2={eje: deg}
            )


def main():
    catalog = lab.load_catalog()
    OUT.mkdir(parents=True, exist_ok=True)
    filas = []
    with sync_playwright() as p:
        browser = c_lab.launch(p)
        page = lab.open_lab(browser, catalog)
        unit = c_lab.scales(page)
        for nombre, pose in casos():
            lab.apply_pose(page, pose)
            v = lab.vectors(page, side="right")
            m = c_lab.metrics(page, unit)
            m.update(extra_metrics(page, unit))
            # Altura de la punta del pulgar respecto a su base, en largos de dedo.
            m["alto"] = round((v["thumbTip"][1] - v["thumb1"][1]) / unit["dedo"], 3)
            m["caso"] = nombre
            filas.append(m)
            print(
                f"{nombre:12s} alto={m['alto']:+.3f} arriba={m['arriba']:+.3f} "
                f"abertura={m['abertura']:.3f} dy={m['dy']:+.3f} curva={m['curva']:.3f}",
                flush=True,
            )
        browser.close()
    (OUT / "metricas.json").write_text(
        json.dumps(filas, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
