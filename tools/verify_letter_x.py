"""Verifica la X tal y como sale en practica.html: gancho y jalon diagonal.

La X tiene dos cosas que comprobar:

  1. la forma: indice en gancho (PIP ~95), medio/anular/menique en puno,
     perfil con la palma hacia el cuerpo.
  2. el trazo: el ciclo jala toda la mano en diagonal arriba-derecha
     (~0.4 palmas a la derecha, ~0.5 arriba) y regresa. No es un giro
     de muneca: el gancho no cambia de forma.
"""
import json
import math
import time
from pathlib import Path

from enfoque_r import MANO, captura, hoja
from pose_lab_e import free_camera
from pose_lab_x import MEASURE_JS, REF, asegurar_ref, linea
from pose_lab_x2 import POS_JS, cam
from pose_lab_x4 import FIST_JS
from playwright.sync_api import sync_playwright
from ver_s import CAM_FOV, CAM_ORBIT, CAM_TARGET
import search_e9 as se9
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "verify_x"
OUT.mkdir(parents=True, exist_ok=True)

se9.URL = "http://127.0.0.1:8006/practica.html?letra=X&v=vx3"

FORMA = {
    "hookPIP": (82.0, 110.0),
    "hookDIP": (50.0, 80.0),
    "idxLen": (0.30, 0.55),
    "puno": (0.0, 0.40),
    "fistUp": (0.75, 1.05),
    "idxSide": (0.55, 0.95),
}
TRAZO = {
    "dx": (0.25, 0.60),
    "dy": (0.35, 0.80),
    "diag": (35.0, 70.0),  # angulo de la diagonal, 45 = arriba-derecha puro
}


def rango(nombre, valor, lo, hi):
    bien = lo <= valor <= hi
    print(f"  {nombre:10s} {valor:+8.2f}  [{lo}, {hi}]  {'ok' if bien else 'FALLA'}")
    return bien


def periodo():
    catalogo = json.loads((ROOT / "data" / "catalogo-lsm.json").read_text("utf-8"))
    c = next(s for s in catalogo["senas"] if s["letra"] == "X")["ciclo"]
    return sum(c[k] for k in ("holdStartMs", "durationMs", "holdEndMs", "resetMs")) / 1000


def main():
    ref = asegurar_ref()
    ciclo_s = periodo()
    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 1100, "height": 900})
        time.sleep(0.3)
        viewer = page.query_selector("#viewer")
        free_camera(page)
        cam(page)

        page.evaluate("() => window.__LSM_CONTROLLER__.mostrarSena('X')")
        time.sleep(2.6)

        m = page.evaluate(MEASURE_JS)
        print("forma de la X:")
        print(" ", linea("X", m))
        ok = True
        ok &= rango("hookPIP", m["hookPIP"], *FORMA["hookPIP"])
        ok &= rango("hookDIP", m["hookDIP"], *FORMA["hookDIP"])
        ok &= rango("idxLen", m["idxLen"], *FORMA["idxLen"])
        ok &= rango("puno", m["puno"], *FORMA["puno"])
        ok &= rango("idxSide", m["idxSide"], *FORMA["idxSide"])
        f = page.evaluate(FIST_JS)
        print(" ", f"fistUp={f['fistUp']:+.2f} fwd={f['fistFwd']:+.2f}")
        ok &= rango("fistUp", f["fistUp"], *FORMA["fistUp"])

        origen = page.evaluate(POS_JS)
        palm = origen["palm"]
        puntos = []
        fin = time.time() + ciclo_s
        while time.time() < fin:
            q = page.evaluate(POS_JS)
            puntos.append((
                (q["x"] - origen["x"]) / palm,
                (q["y"] - origen["y"]) / palm,
            ))
            time.sleep(0.04)
        xs = [q[0] for q in puntos]
        ys = [q[1] for q in puntos]
        dx = max(xs) - min(xs)
        dy = max(ys) - min(ys)
        # el tramo de ida (crece y): angulo medio de los pasos que suben
        angs = []
        for (x0, y0), (x1, y1) in zip(puntos, puntos[1:]):
            if y1 - y0 > 0.002:
                angs.append(math.degrees(math.atan2(y1 - y0, x1 - x0)))
        diag = sum(angs) / len(angs) if angs else 0.0
        print(f"\ntrazo ({len(puntos)} muestras en {ciclo_s:.2f} s de ciclo):")
        ok &= rango("dx", dx, *TRAZO["dx"])
        ok &= rango("dy", dy, *TRAZO["dy"])
        ok &= rango("diag", diag, *TRAZO["diag"])

        rotulo = page.inner_text("#anim-info").strip()
        print("\n  " + ("TODO OK" if ok else "REVISAR"))
        print("  rotulo:", rotulo[:140])

        items = [("REF foto", ref)] if ref else []
        ruta = OUT / "X_forma.png"
        captura(page, ruta, huesos=MANO, margen=0.45, lado=420)
        items.append(("X forma", ruta))
        viewer.screenshot(path=str(OUT / "X_produccion.png"))

        # tira del jalon
        tira = []
        page.evaluate("() => window.__LSM_CONTROLLER__.mostrarSena('X')")
        time.sleep(2.5)
        for i in range(8):
            r = OUT / f"X_{i:02d}.png"
            captura(page, r, huesos=MANO, margen=0.55, lado=360)
            tira.append((f"X_{i:02d}", r))
            time.sleep(0.28)
        hoja(
            ([("REF foto", ref)] if ref else []) + tira,
            OUT / "_ciclo.png",
            cols=3,
            cell=340,
            titulo="X · ciclo en practica.html",
        )
        hoja(items, OUT / "_forma.png", cols=2, cell=400, titulo="X verificada")

        browser.close()
    print("Capturas en", OUT)
    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
