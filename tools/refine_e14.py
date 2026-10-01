"""Afinado del pulgar de la E alrededor de la zona buena de search_e14.

En search_e14 el pulgar ya se queda del lado del indice y apunta hacia arriba,
pero su punta acaba MAS ALTA que las yemas (`bajo` negativo) y por eso parece un
quinto dedo. En la foto de referencia la punta del pulgar queda a media palma,
justo por debajo de la yema del indice. Aqui se le sube el peso a esa medida y
se anaden dobleces mayores del propio pulgar, que es lo que mantiene la punta
baja mientras la base sube por el borde de la mano.
"""
import itertools
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

from search_e11 import MEASURE_JS
from search_e13 import pose_e, score_dedos
from search_e14 import linea
from search_e9 import abrir, banda

ROOT = Path(__file__).resolve().parents[1]


def score_pulgar(m):
    p = 0.0
    # la punta del pulgar por DEBAJO de las yemas: es lo que evita que parezca
    # un quinto dedo levantado
    p += 8.0 * banda(m["pulgarBajoYemas"], 0.04, 0.26)
    # cerca de la yema del indice, que es donde se apoya
    p += 6.0 * banda(m["tipoI"], 0.08, 0.30)
    # del lado del indice, sin barrer la palma
    p += 6.0 * banda(m["across"], -0.05, 0.35)
    # inclinado hacia los dedos, no atravesado
    p += 4.0 * banda(m["pulgarArriba"], 0.15, 0.85)
    # por delante de la palma pero pegado a ella
    p += 3.0 * banda(m["thumbFrente"], 0.10, 0.45)
    return p


def main():
    with sync_playwright() as p:
        browser, page = abrir(p)

        def ev(pose):
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
            return page.evaluate(MEASURE_JS)

        rejilla = list(
            itertools.product(
                (0.5, 0.65, 0.8, 0.95),      # tcurl
                (-0.6, -0.3),                # aside
                (-50, -40, -30),             # t1x
                (-30, -15, 0),               # t1y
                (-30, -20, -10, 0),          # t1z
                (0, 25, 50, 75),             # t2x
                (25, 50, 75),                # t3x
            )
        )
        print(f"Afinado del pulgar: {len(rejilla)}")
        res = []
        for tcurl, aside, t1x, t1y, t1z, t2x, t3x in rejilla:
            m = ev(pose_e(0.88, -4, tcurl, aside, t1x, t1y, t1z, t2x, t3x))
            res.append(
                (
                    score_dedos(m) + score_pulgar(m),
                    (tcurl, aside, t1x, t1y, t1z, t2x, t3x),
                    m,
                )
            )
        res.sort(key=lambda t: t[0])
        print("MEJORES")
        for sc, t, m in res[:20]:
            print(
                " ",
                linea(
                    f"tc{t[0]} a{t[1]} x{t[2]} y{t[3]} z{t[4]} t2{t[5]} t3{t[6]}", m, sc
                ),
            )
        browser.close()

    out = ROOT / "tools" / "screenshots" / "refine_e14.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(
            [{"score": sc, "pulgar": t, "m": m} for sc, t, m in res[:40]], indent=2
        ),
        "utf-8",
    )
    print("\n->", out)


if __name__ == "__main__":
    main()
