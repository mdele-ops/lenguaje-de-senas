"""P: busca el giro del pulgar que deja la YEMA pegada al dedo medio.

Mide con la malla (piel_p.PIEL_JS), no con el esqueleto: se pide que el hueco
minimo entre las pieles sea ~0, que varios vertices de la punta del pulgar
queden a menos de 2 mm del medio (contacto con superficie, no con un punto) y
que el pulgar no se meta en el indice. El esqueleto (pulgar_p.CONTACTO_JS) solo
vigila que la punta no atraviese el dedo.

Uso: python _run.py busca_p.py [iteraciones]
"""
import json
import random
import sys
import time

from playwright.sync_api import sync_playwright

import pulgar_p as pp
import piel_p
import search_e9 as se9
from search_e9 import abrir

se9.URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=bp"


def evalua(page, base, c):
    pp.aplicar(page, pp.pose_de(c, base))
    sk = page.evaluate(pp.CONTACTO_JS)
    piel = page.evaluate(piel_p.PIEL_JS)
    return sk, piel


def puntaje(c, c0, sk, piel):
    a = piel["area"]
    c_ = piel["contacto"]
    pos = sk["seg"] + sk["t"]
    reg = sum(abs(c[k] - c0[k]) / (0.3 if k in ("tcurl", "taside") else 30.0) for k in c0)
    return (
        # hueco minimo ~0 (la malla ya no deja menos de ~1 mm entre vertices)
        400.0 * max(0.0, piel["gapMedio"] - 0.0005)
        # superficie de contacto: muchos vertices a < 2 mm
        + 0.15 * max(0, 14 - a["mm2"])
        + 0.15 * max(0.0, a["k15"] - 1.2)
        # la punta no atraviesa el dedo (esqueleto)
        + 6.0 * max(0.0, 0.05 - sk["best"])
        # sin meterse en el indice
        + 40.0 * max(0.0, 0.010 - piel["gapIndice"])
        # el contacto es con la punta del pulgar, sobre el dedo medio (M2-M3)
        + 2.0 * max(0.0, c_["aT4"] - 0.18)
        + 0.4 * max(0.0, 0.5 - pos) + 0.4 * max(0.0, pos - 1.3)
        + 0.01 * reg
    )


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 600
    base = pp.pose_catalogo()
    c0 = pp.inicio(base)
    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 900, "height": 700})
        time.sleep(0.5)
        sk, piel = evalua(page, base, c0)
        s0 = puntaje(c0, c0, sk, piel)
        print(f"BASE score={s0:.3f} gap={piel['gapMedio']*1000:.2f}mm "
              f"area={piel['area']} sk={sk['best']:.3f}", flush=True)
        random.seed(11)
        mejor = (s0, c0, piel)
        for it in range(n):
            ref = mejor[1] if random.random() < 0.8 else c0
            c = dict(ref)
            esc = 1.0 if it < n * 0.4 else 0.3
            for k, w in (("tcurl", 0.15), ("taside", 0.2), ("t1x", 12), ("t1y", 12),
                         ("t1z", 12), ("t2x", 10), ("t2y", 8), ("t2z", 10),
                         ("t3x", 10), ("t3y", 8), ("t3z", 6)):
                if random.random() < 0.5:
                    c[k] = c[k] + random.gauss(0, w * esc)
            c["tcurl"] = max(0.0, min(1.0, c["tcurl"]))
            c["taside"] = max(-1.0, min(1.0, c["taside"]))
            sk, piel = evalua(page, base, c)
            s = puntaje(c, c0, sk, piel)
            if s < mejor[0]:
                mejor = (s, c, piel)
                print(f"{it:4d} score={s:.3f} gap={piel['gapMedio']*1000:.2f}mm "
                      f"area={piel['area']} sk={sk['best']:.3f} "
                      f"idx={piel['gapIndice']*1000:.1f}mm", flush=True)
        print(json.dumps(mejor[1], indent=1))
        (pp.OUT / "mejor_piel.json").write_text(json.dumps(mejor[1], indent=2), "utf-8")
        browser.close()


if __name__ == "__main__":
    main()
