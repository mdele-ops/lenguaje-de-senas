"""Busqueda de la E con el pulgar bien entendido.

Mirando la foto de referencia a tamano completo: el pulgar NO cruza la palma de
lado a lado. Se dobla hacia ARRIBA por el lado del indice, con la punta (se le
ve la una) a media altura de la palma, justo debajo de la yema del indice. Las
busquedas anteriores lo tumbaban atravesado porque se les pidio que las CUATRO
yemas lo tocaran, y para eso tenia que barrer toda la mano.

Los dedos son el puno de la A/S sin cerrar del todo (`curl` ~0.9), separados.
"""
import itertools
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

from search_e11 import MEASURE_JS
from search_e13 import pose_e, score_dedos
from search_e9 import abrir, banda

ROOT = Path(__file__).resolve().parents[1]


def score_pulgar(m):
    p = 0.0
    # el pulgar apunta hacia los dedos, no atravesado
    p += 6.0 * banda(m["pulgarArriba"], 0.40, 1.00)
    # se queda del lado del indice (0 = indice, 1 = menique)
    p += 6.0 * banda(m["across"], -0.05, 0.35)
    # su punta llega justo bajo la yema del indice
    p += 6.0 * banda(m["tipoI"], 0.08, 0.32)
    # por delante de la palma, pegado a ella
    p += 3.0 * banda(m["thumbFrente"], 0.10, 0.50)
    # y por debajo de las yemas, que se apoyan encima
    p += 3.0 * banda(m["pulgarBajoYemas"], 0.02, 0.30)
    return p


def linea(nombre, m, score):
    return (
        f"{nombre:44s} sc={score:6.3f} baja={m['baja']:.2f} sep={m['sep']:.3f} | "
        f"arriba={m['pulgarArriba']:+.2f} across={m['across']:+.2f} "
        f"tipoI={m['tipoI']:.2f} frente={m['thumbFrente']:+.2f} "
        f"bajo={m['pulgarBajoYemas']:+.2f} tLen={m['thumbLen']:.2f}"
    )


def main():
    cat = json.loads((ROOT / "data" / "catalogo-lsm.json").read_text("utf-8"))
    senas = {s["letra"]: s for s in cat["senas"]}

    with sync_playwright() as p:
        browser, page = abrir(p)

        def ev(pose):
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
            return page.evaluate(MEASURE_JS)

        for letra in ("E", "A", "S"):
            m = ev(senas[letra]["pose"])
            print(f"{letra:>2s}:", linea(letra, m, score_dedos(m) + score_pulgar(m)))
        print()

        # Dedos fijos: el puno de la A/S sin cerrar del todo, separados.
        DEDOS = [(0.92, -4), (0.92, 0), (0.88, -4)]

        rejilla = list(
            itertools.product(
                (0.2, 0.35, 0.5, 0.65, 0.8),   # tcurl
                (-0.6, -0.3, 0.0, 0.3),        # aside
                (-40, -20, 0, 20),             # t1x
                (-30, -15, 0, 15),             # t1y
                (-20, 0, 20),                  # t1z
                (0, 25, 50),                   # t2x
                (0, 25, 50),                   # t3x
            )
        )
        print(f"Pulgar: {len(rejilla)} x {len(DEDOS)} dedos")
        res = []
        for curl, conv in DEDOS:
            for tcurl, aside, t1x, t1y, t1z, t2x, t3x in rejilla:
                m = ev(pose_e(curl, conv, tcurl, aside, t1x, t1y, t1z, t2x, t3x))
                res.append(
                    (
                        score_dedos(m) + score_pulgar(m),
                        ((curl, conv), (tcurl, aside, t1x, t1y, t1z, t2x, t3x)),
                        m,
                    )
                )
        res.sort(key=lambda t: t[0])
        print("MEJORES")
        for sc, k, m in res[:18]:
            d, t = k
            print(
                " ",
                linea(
                    f"c{d[0]}v{d[1]}|tc{t[0]} a{t[1]} x{t[2]} y{t[3]} z{t[4]} t2{t[5]} t3{t[6]}",
                    m, sc,
                ),
            )
        browser.close()

    out = ROOT / "tools" / "screenshots" / "search_e14.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(
            [{"score": sc, "dedos": k[0], "pulgar": k[1], "m": m} for sc, k, m in res[:40]],
            indent=2,
        ),
        "utf-8",
    )
    print("\n->", out)


if __name__ == "__main__":
    main()
