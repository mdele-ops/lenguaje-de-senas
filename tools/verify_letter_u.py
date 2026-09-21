"""Verifica la U por el camino real de la app (mostrarSena).

La U del catalogo dejaba indice y medio separados (se leia como una V suave)
y el pulgar al costado del indice. Ahora los dos dedos largos se juntan sin
cruzarse y el pulgar va tumbado sobre anular y menique, como en la foto.
"""
import time
from pathlib import Path

from eje_r import CAM_FOV, CAM_ORBIT, CAM_TARGET, cam, encuadrar
from enfoque_r import MANO, captura, hoja
from pose_lab_e import free_camera
from pose_lab_r import MEASURE_JS
from pose_lab_u import linea
from search_e9 import abrir
import search_e9 as se9

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "verify_u"
OUT.mkdir(parents=True, exist_ok=True)
REF = ROOT / "tools" / "screenshots" / "lab_u2" / "_ref.png"

se9.URL = "http://127.0.0.1:8006/practica.html?letra=U&v=uverify3"


def main():
    with sync_playwright_open() as (browser, page):
        page.set_viewport_size({"width": 900, "height": 900})
        free_camera(page)
        viewer = page.query_selector("#viewer")

        page.evaluate("() => window.__LSM_CONTROLLER__.mostrarSena('U')")
        time.sleep(2.6)

        rotulo = page.inner_text("#anim-info").strip()[:180]
        print("  rotulo:", rotulo)

        m = page.evaluate(MEASURE_JS)
        if m.get("error"):
            print("  medida:", m)
        else:
            print(" ", linea("U catalogo", m))
            print(
                f"  cruce={m['cruce']:+.2f} (debe ser <0, si no es R)  "
                f"yemas={m['sepYemas']:.3f} gap={m['gap']:.3f}  "
                f"thLat={m['thLat']:+.2f} (positivo = sobre anular)"
            )

        items = [("REF foto", REF)] if REF.exists() else []
        cam(page, CAM_TARGET, CAM_ORBIT, CAM_FOV)
        prod = OUT / "U_prod.png"
        viewer.screenshot(path=str(prod))
        items.append(("U produccion", prod))

        encuadrar(page, 0)
        mano = OUT / "U_mano.png"
        captura(page, mano, MANO, margen=0.22, lado=560)
        items.append(("U mano", mano))

        encuadrar(page, -40)
        lado = OUT / "U_34.png"
        captura(page, lado, MANO, margen=0.22, lado=560)
        items.append(("U 3/4", lado))

        browser.close()

    hoja(items, OUT / "_hoja.png", cols=2, cell=420, titulo="U · verificar catalogo")
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
