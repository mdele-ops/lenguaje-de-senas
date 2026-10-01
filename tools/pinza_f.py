"""F: buscar la pose donde las yemas de pulgar e indice se toquen de verdad.

Barrido grueso sobre lo que mueve la pinza (curl y aside del pulgar, curl y
spread del indice, y el giro extra del trapecio) midiendo con `junta_f.PINZA_JS`.
Se pide contacto en las puntas (dondeT/dondeI cerca de 1), falanges distales
enfrentadas y los otros tres dedos estirados.
"""
import itertools
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from junta_f import PINZA_JS, informe
from lab_e2 import abrir, preparar, publicar, retratar

OUT = Path(__file__).resolve().parents[1] / "tools" / "screenshots" / "pinza_f"

T1 = "RightHandThumb1"
I2 = "RightHandIndex2"


def pose(tc, ta, ic, isp, t1z):
    return {
        "thumb": {"curl": tc, "aside": ta},
        "index": {"curl": ic, "spread": isp},
        "middle": {"curl": 0.0, "spread": 3},
        "ring": {"curl": 0.0, "spread": 4},
        "pinky": {"curl": 0.0, "spread": 6},
        "extra": {T1: {"z": t1z}},
    }


REJILLA = list(
    itertools.product(
        (0.2, 0.35, 0.5, 0.65, 0.8),   # curl pulgar
        (-0.2, 0.0, 0.2, 0.4, 0.6),    # aside pulgar
        (0.45, 0.55, 0.65, 0.75),      # curl indice
        (0, 8, 16),                    # spread indice
        (10, 30, 50),                  # z extra del trapecio
    )
)


def puntua(m):
    """Menor es mejor. Contacto de yemas cerca de 0.06 palmas, bien enfrentadas."""
    castigo = 0.0
    if m["enfrentados"] < 80:
        castigo += (80 - m["enfrentados"]) * 0.004
    for donde in (m["dondeT"], m["dondeI"]):
        if donde < 0.8:
            castigo += (0.8 - donde) * 0.5
    peor = max(m["estirados"])
    if peor > 40:
        castigo += (peor - 40) * 0.004
    return abs(m["puntas"] - 0.06) + castigo


def main():
    with sync_playwright() as p:
        browser, page = abrir(p)
        viewer = preparar(page)

        filas = []
        for i, combo in enumerate(REJILLA):
            page.evaluate(
                "(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose(*combo)
            )
            m = page.evaluate(PINZA_JS)
            if m.get("error"):
                raise SystemExit(m)
            filas.append((puntua(m), combo, m))
            if i % 60 == 0:
                print(f"  {i}/{len(REJILLA)}")

        filas.sort(key=lambda f: f[0])
        print("mejores:")
        for score, combo, m in filas[:12]:
            tc, ta, ic, isp, t1z = combo
            nombre = f"tc{tc}_ta{ta}_ic{ic}_sp{isp}_z{t1z}"
            print(f"  {score:.3f} " + informe(nombre, m))

        salida = {}
        for score, combo, m in filas[:6]:
            tc, ta, ic, isp, t1z = combo
            nombre = f"{score:.3f}_tc{tc}_ta{ta}_ic{ic}_sp{isp}_z{t1z}"
            page.evaluate(
                "(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose(*combo)
            )
            time.sleep(0.3)
            retratar(page, viewer, nombre, OUT, salida)
        browser.close()

    for h in publicar(salida, OUT, refs=()):
        print("hoja:", h)


if __name__ == "__main__":
    main()
