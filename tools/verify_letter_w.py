"""Verifica la W por el camino real de la app (mostrarSena).

El tridente queda cerrado (~15 deg entre huecos vecinos en 3D) para que
no se lea como abanico, y el pulgar va tumbado sobre el meñique.
"""
import time
from pathlib import Path

from eje_r import CAM_FOV, CAM_ORBIT, CAM_TARGET, cam, encuadrar
from enfoque_r import MANO, captura, hoja
from pose_lab_e import free_camera
from pose_lab_r import MEASURE_JS
from pose_lab_w import ANGLE_JS, linea
from search_e9 import abrir
import search_e9 as se9

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "verify_w"
OUT.mkdir(parents=True, exist_ok=True)
REF = ROOT / "tools" / "screenshots" / "referencia" / "W_usuario.png"

se9.URL = "http://127.0.0.1:8006/practica.html?letra=W&v=wverify2"


def main():
    with sync_playwright_open() as (browser, page):
        page.set_viewport_size({"width": 900, "height": 900})
        free_camera(page)
        viewer = page.query_selector("#viewer")

        page.evaluate("() => window.__LSM_CONTROLLER__.mostrarSena('W')")
        time.sleep(2.6)

        rotulo = page.inner_text("#anim-info").strip()[:180]
        print("  rotulo:", rotulo)

        m = page.evaluate(MEASURE_JS)
        a = page.evaluate(ANGLE_JS)
        if m.get("error"):
            print("  medida:", m)
        else:
            print(" ", linea("W catalogo", m, a))
            print(
                f"  angIM={a['angIM']:.1f}/{a.get('angPxIM')}  "
                f"angMR={a['angMR']:.1f}/{a.get('angPxMR')}  "
                f"(huecos 3D ~15, foto tres palitos)  "
                f"sep={a['sepIM']:.2f}/{a['sepMR']:.2f}  "
                f"thLat={m['thLat']:+.2f} thP={a['thumbPinky']:.2f}"
            )

        items = [("REF foto", REF)] if REF.exists() else []
        cam(page, CAM_TARGET, CAM_ORBIT, CAM_FOV)
        prod = OUT / "W_prod.png"
        viewer.screenshot(path=str(prod))
        items.append(("W produccion", prod))

        mano = OUT / "W_mano.png"
        captura(page, mano, MANO, margen=0.28, lado=560)
        items.append(("W mano", mano))

        encuadrar(page, 0, holgura=3.8)
        zoom = OUT / "W_zoom.png"
        viewer.screenshot(path=str(zoom))
        items.append(("W zoom", zoom))

        encuadrar(page, -40, holgura=3.8)
        lado = OUT / "W_34.png"
        viewer.screenshot(path=str(lado))
        items.append(("W 3/4", lado))

        browser.close()

    hoja(items, OUT / "_hoja.png", cols=2, cell=420, titulo="W · verificar catalogo")
    print("Capturas en", OUT)


def sync_playwright_open():
    from playwright.sync_api import sync_playwright

    class Ctx:
        def __enter__(self):
            self.p = sync_playwright().start()
            self.browser, self.page = abrir(self.p)
            return self.browser, self.page

        def __exit__(self, *a):
            self.p.stop()

    return Ctx()


if __name__ == "__main__":
    main()
