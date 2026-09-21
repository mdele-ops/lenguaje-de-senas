"""Verifica la V por el camino real de la app (mostrarSena).

La V del catalogo dejaba indice y medio a +-42 de spread (peace sign) y el
pulgar de pie al costado. Ahora la V es estrecha (~31 deg en pantalla) y el
pulgar va tumbado sobre anular y menique, como en la foto.
"""
import time
from pathlib import Path

from eje_r import CAM_FOV, CAM_ORBIT, CAM_TARGET, cam, encuadrar
from enfoque_r import MANO, captura, hoja
from pose_lab_e import free_camera
from pose_lab_r import MEASURE_JS
from pose_lab_v import ANGLE_JS, linea
from search_e9 import abrir
import search_e9 as se9

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "verify_v"
OUT.mkdir(parents=True, exist_ok=True)
REF = ROOT / "tools" / "screenshots" / "referencia" / "V_usuario.png"

se9.URL = "http://127.0.0.1:8006/practica.html?letra=V&v=vverify1"


def main():
    with sync_playwright_open() as (browser, page):
        page.set_viewport_size({"width": 900, "height": 900})
        free_camera(page)
        viewer = page.query_selector("#viewer")

        page.evaluate("() => window.__LSM_CONTROLLER__.mostrarSena('V')")
        time.sleep(2.6)

        rotulo = page.inner_text("#anim-info").strip()[:180]
        print("  rotulo:", rotulo)

        m = page.evaluate(MEASURE_JS)
        a = page.evaluate(ANGLE_JS)
        if m.get("error"):
            print("  medida:", m)
        else:
            print(" ", linea("V catalogo", m, a))
            print(
                f"  ang3d={a['ang3d']:.1f} angPx={a.get('angPx')}  "
                f"(foto ~30-35 deg)  yemas={m['sepYemas']:.3f}  "
                f"thLat={m['thLat']:+.2f} (positivo = sobre anular)"
            )

        items = [("REF foto", REF)] if REF.exists() else []
        cam(page, CAM_TARGET, CAM_ORBIT, CAM_FOV)
        prod = OUT / "V_prod.png"
        viewer.screenshot(path=str(prod))
        items.append(("V produccion", prod))

        encuadrar(page, 0)
        mano = OUT / "V_mano.png"
        captura(page, mano, MANO, margen=0.22, lado=560)
        items.append(("V mano", mano))

        encuadrar(page, -40)
        lado = OUT / "V_34.png"
        captura(page, lado, MANO, margen=0.22, lado=560)
        items.append(("V 3/4", lado))

        browser.close()

    hoja(items, OUT / "_hoja.png", cols=2, cell=420, titulo="V · verificar catalogo")
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
