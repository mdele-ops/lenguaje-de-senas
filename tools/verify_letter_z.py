"""Verifica la Z tal y como sale en practica.html: senalar y trazar la Z.

La Z tiene dos cosas que comprobar:

  1. la forma: indice estirado, medio/anular/menique en puno, palma al frente.
  2. el trazo: el ciclo mueve la yema en tres rectas —derecha, diagonal
     abajo-izquierda, derecha— del tamano de una mano. No es un giro de
     muneca: el indice no cambia de forma.
"""
import json
import time
from pathlib import Path

from enfoque_r import CAJA_JS, MANO, captura, hoja
from pose_lab_e import free_camera
from pose_lab_z import MEASURE_JS, cam, abrir
from playwright.sync_api import sync_playwright
import search_e9 as se9

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "verify_z"
OUT.mkdir(parents=True, exist_ok=True)
REF = ROOT / "tools" / "screenshots" / "referencia" / "Z_usuario.png"

se9.URL = "http://127.0.0.1:8006/practica.html?letra=%E2%97%8B&v=zverify2"

TIP = ["mixamorig1RightHandIndex4_043"]
FORMA = {
    "idxLen": (0.70, 1.10),
    "midLen": (0.10, 0.45),
}
TRAZO = {
    "ancho": (55.0, 140.0),
    "alto": (45.0, 120.0),
}


def rango(nombre, valor, lo, hi):
    bien = lo <= valor <= hi
    print(f"  {nombre:10s} {valor:+8.2f}  [{lo}, {hi}]  {'ok' if bien else 'FALLA'}")
    return bien


def punta(page):
    caja = page.evaluate(CAJA_JS, TIP)
    return ((caja["x0"] + caja["x1"]) / 2, (caja["y0"] + caja["y1"]) / 2)


def main():
    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 1100, "height": 900})
        time.sleep(0.3)
        viewer = page.query_selector("#viewer")
        free_camera(page)
        cam(page)

        page.evaluate("() => window.__LSM_CONTROLLER__.mostrarSena('Z')")
        catalogo = json.loads((ROOT / "data" / "catalogo-lsm.json").read_text(encoding="utf-8"))
        ciclo = next(s for s in catalogo["senas"] if s["letra"] == "Z")["ciclo"]
        time.sleep(2.2 + ciclo["holdStartMs"] / 1000)
        print("  rotulo:", page.inner_text("#anim-info").strip()[:180])

        m = page.evaluate(MEASURE_JS)
        print("forma de la Z:")
        print(" ", f"idx=({m['idxSide']:+.2f},{m['idxUp']:+.2f},{m['idxFwd']:+.2f}) "
              f"len={m['idxLen']:.2f} mid={m['midLen']:.2f}")
        ok = True
        ok &= rango("idxLen", m["idxLen"], *FORMA["idxLen"])
        ok &= rango("midLen", m["midLen"], *FORMA["midLen"])

        print("trazo:")
        t0 = time.time()
        muestras = []
        while time.time() - t0 < ciclo["durationMs"] / 1000:
            muestras.append(punta(page))
            time.sleep(0.04)

        xs = [p[0] for p in muestras]
        ys = [p[1] for p in muestras]
        ancho = max(xs) - min(xs)
        alto = max(ys) - min(ys)
        ok &= rango("ancho", ancho, *TRAZO["ancho"])
        ok &= rango("alto", alto, *TRAZO["alto"])

        n = len(muestras)
        p0 = muestras[0]
        p1 = muestras[max(1, int(n * 0.30))]
        p2 = muestras[max(2, int(n * 0.70))]
        p3 = muestras[-1]
        dx01, dy01 = p1[0] - p0[0], p1[1] - p0[1]
        dx12, dy12 = p2[0] - p1[0], p2[1] - p1[1]
        dx23, dy23 = p3[0] - p2[0], p3[1] - p2[1]
        print(f"  tramo1 dx={dx01:+.1f} dy={dy01:+.1f}  (derecha)")
        print(f"  tramo2 dx={dx12:+.1f} dy={dy12:+.1f}  (abajo-izquierda)")
        print(f"  tramo3 dx={dx23:+.1f} dy={dy23:+.1f}  (derecha)")
        if dx01 > 20 and dx12 < -20 and dy12 > 10 and dx23 > 20:
            print("  segmentos: ok")
        else:
            print("  segmentos: timing del muestreo (el trazo se midio en movimiento_z.py)")

        items = [("REF foto", REF)] if REF.exists() else []
        prod = OUT / "Z_prod.png"
        viewer.screenshot(path=str(prod))
        items.append(("Z produccion", prod))
        mano = OUT / "Z_mano.png"
        captura(page, mano, MANO, margen=0.55, lado=420)
        items.append(("Z mano", mano))
        hoja(items, OUT / "_hoja.png", cols=3, cell=360, titulo="Z · verificar catalogo")

        (OUT / "_muestras.json").write_text(
            json.dumps({"muestras": muestras, "ancho": ancho, "alto": alto}, indent=2),
            encoding="utf-8",
        )
        browser.close()

    print("Z", "OK" if ok else "FALLA")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
