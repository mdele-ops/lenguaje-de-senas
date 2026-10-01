"""Verifica la X tal y como sale en practica.html: gancho y jalon al pecho.

La X tiene dos cosas que comprobar:

  1. la forma: indice en gancho (PIP ~95), medio/anular/menique en puno,
     perfil con la palma hacia el cuerpo.
  2. el trazo: el ciclo jala toda la mano hacia atras, hacia el pecho
     (~0.5-1.0 palmas mas cerca), y regresa. Se mide contra el pecho
     (Spine2) porque la camara sigue a la mano. No es un giro de muneca:
     el gancho no cambia de forma.
"""
import json
import math
import time
from pathlib import Path

from enfoque_r import MANO, captura, hoja
from pose_lab_e import _GET_SCENE, free_camera
from pose_lab_x import MEASURE_JS, REF, asegurar_ref, linea
from pose_lab_x2 import cam
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
    "acerca": (0.50, 1.00),  # palmas que la mano se acerca al pecho (hacia atras)
    "lateral": (0.0, 0.60),  # palmas hacia la linea media (poco)
    "sube": (0.0, 0.30),     # casi no sube ni baja
}

# Posicion del nudillo del indice RELATIVA al pecho, en palmas. La camara
# sigue a la mano, asi que en coordenadas del mundo el jalon no se ve.
PECHO_JS = (
    """
() => {
  const mv = document.getElementById('handViewer');
"""
    + _GET_SCENE
    + """
  const scene = getScene(mv);
  scene.updateMatrixWorld(true);
  const B = {};
  scene.traverse((o) => { if (o && o.name) B[o.name] = o; });
  const P = (n) => {
    const e = B[n].matrixWorld.elements;
    return { x: e[12], y: e[13], z: e[14] };
  };
  const s = P('Spine2');
  const w = P('RightHand');
  const k = P('RightHandIndex1');
  const palm = Math.hypot(w.x - k.x, w.y - k.y, w.z - k.z) || 1;
  return {
    x: (k.x - s.x) / palm,
    y: (k.y - s.y) / palm,
    z: (k.z - s.z) / palm,
  };
}
"""
)


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

        puntos = []
        fin = time.time() + ciclo_s
        while time.time() < fin:
            puntos.append(page.evaluate(PECHO_JS))
            time.sleep(0.04)
        zs = [q["z"] for q in puntos]
        xs = [q["x"] for q in puntos]
        ys = [q["y"] for q in puntos]
        # z es la distancia al pecho (hacia el frente): jalar = que baje
        acerca = max(zs) - min(zs)
        lateral = max(xs) - min(xs)
        sube = max(ys) - min(ys)
        print(f"\ntrazo ({len(puntos)} muestras en {ciclo_s:.2f} s de ciclo):")
        ok &= rango("acerca", acerca, *TRAZO["acerca"])
        ok &= rango("lateral", lateral, *TRAZO["lateral"])
        ok &= rango("sube", sube, *TRAZO["sube"])

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
