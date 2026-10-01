"""Verifica la letra P desde el boton real de practica.html.

No basta con que la escuadra indice-medio exista en el esqueleto:

  - la primera version la formaba bien pero con la mano de tres cuartos, y en
    pantalla el dedo medio salia corto porque apuntaba hacia la camara. De ahi
    el largo APARENTE de los dedos (idxScr/midScr) y el perfil (palmNz ~ 0).
  - la segunda quedaba de perfil pero tiesa, con la mano recta y la escuadra a
    90. De ahi los angulos en pantalla (idxAng/midAng), medidos sobre la foto
    de referencia: indice ~51, medio ~-2, o sea la mano doblada en diagonal.
"""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from pose_lab_e import HAND_POS_JS, free_camera
from pose_lab_p9 import MEASURE_JS
import search_e9 as se9
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "lab_p_final"
OUT.mkdir(parents=True, exist_ok=True)

se9.URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=pfinal"

VISTAS = {
    "produccion": ("0m 2.45m 0.15m", "0deg 84deg 2.5m", "30deg", 0.0),
    "cuerpo": ("0m 2.42m 0.15m", "18deg 84deg 2.0m", "26deg", 0.0),
    "mano": (None, "0deg 84deg 1.40m", "21deg", 0.04),
    "perfil": (None, "-60deg 84deg 0.70m", "24deg", 0.02),
}

# Lo que tiene que cumplirse para que sea una P legible y no otra letra.
CRITERIOS = {
    "idxAng": (44.0, 60.0),      # indice en diagonal, como en la foto (~51)
    "midAng": (-10.0, 5.0),      # dedo medio horizontal (~-2)
    "escuadra": (46.0, 62.0),    # apertura de una mano real, no 90
    "manoAng": (52.0, 72.0),     # eje de la mano inclinado: el doblez
    "palmNz": (-0.20, 0.20),     # palma de canto: si no, se ve de tres cuartos
    "midScr": (0.85, 1.20),      # los dedos se ven a su largo completo
    "idxScr": (0.70, 1.20),
}


def main():
    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 1100, "height": 900})
        time.sleep(0.3)
        viewer = page.query_selector("#viewer")

        page.evaluate("() => window.__LSM_CONTROLLER__.mostrarSena('P')")
        time.sleep(2.6)

        m = page.evaluate(MEASURE_JS)
        print("medidas P:")
        ok = True
        for clave, (lo, hi) in CRITERIOS.items():
            v = m[clave]
            bien = lo <= v <= hi
            ok = ok and bien
            print(f"  {clave:10s} {v:+7.2f}  [{lo}, {hi}]  {'ok' if bien else 'FALLA'}")
        print("  " + ("TODO OK" if ok else "REVISAR"))
        print("  rotulo:", page.inner_text("#anim-info").strip()[:120])

        free_camera(page)
        hand = page.evaluate(HAND_POS_JS)
        for nombre, (target, orbit, fov, dy) in VISTAS.items():
            t = target or "%.3fm %.3fm %.3fm" % (
                hand["x"],
                hand["y"] + dy,
                hand["z"],
            )
            page.evaluate(
                """(a) => {
                    const mv = document.getElementById('handViewer');
                    mv.cameraTarget = a.t;
                    mv.cameraOrbit = a.orbit;
                    mv.fieldOfView = a.fov;
                    mv.jumpCameraToGoal();
                }""",
                {"t": t, "orbit": orbit, "fov": fov},
            )
            time.sleep(0.4)
            viewer.screenshot(path=str(OUT / f"P_{nombre}.png"))

        browser.close()
    print("Capturas en", OUT)


if __name__ == "__main__":
    main()
