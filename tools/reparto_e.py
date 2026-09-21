"""Que reparto mcp/pip/dip deja las yemas donde las tiene la foto.

En la foto la yema queda ~0.21 de palma por debajo de la fila de nudillos: el
puno es compacto, los dedos se enrollan sobre si mismos. En el modelo, con el
reparto que se venia usando (mcp 70 / pip 95 / dip 60) las yemas caen a 0.51, o
sea el dedo baja arrastrandose por la palma y de ahi la lectura de garra.

Este barrido solo mide, no renderiza: para cada objetivo calibra los cuatro
dedos y anota donde acaba la yema.
"""
import itertools
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

from calibra_e import calibrar
from search_e9 import abrir
from simetria_e import SIMETRIA_JS

ROOT = Path(__file__).resolve().parents[1]

# lo que se busca reproducir, medido sobre tools/zoom_ref_e
FOLD_FOTO = 0.21

MCP = (70, 80, 90, 100)
PIP = (95, 105, 115)
DIP = (60, 75, 90)
CONV = 8


def main():
    with sync_playwright() as p:
        browser, page = abrir(p)

        def sim(pz):
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pz)
            return page.evaluate(SIMETRIA_JS)

        res = []
        for mcp, pip, dip in itertools.product(MCP, PIP, DIP):
            corr, s = calibrar(
                sim, 0.0, CONV,
                objetivo={"mcp": mcp, "pip": pip, "dip": dip},
                verbose=False,
            )
            res.append((abs(s["foldMedia"] - FOLD_FOTO), (mcp, pip, dip), corr, s))
            print(
                f"mcp{mcp:3d} pip{pip:3d} dip{dip:3d} -> fold={s['foldMedia']:+.3f} "
                f"front={s['frontMedia']:+.3f} gap={s['gapMin']:.3f} "
                f"foldD={s['foldDisp']:.3f}"
            )
        res.sort(key=lambda t: t[0])
        print(f"\nmas cerca de fold={FOLD_FOTO}:")
        for err, k, _, s in res[:8]:
            print(
                f"  mcp{k[0]} pip{k[1]} dip{k[2]}  fold={s['foldMedia']:+.3f} "
                f"front={s['frontMedia']:+.3f} (error {err:.3f})"
            )
        browser.close()

    out = ROOT / "tools" / "screenshots" / "reparto_e.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(
            [
                {"objetivo": k, "correcciones": c, "medidas": s}
                for _, k, c, s in res
            ],
            indent=2,
        ),
        "utf-8",
    )
    print("\n->", out)


if __name__ == "__main__":
    main()
