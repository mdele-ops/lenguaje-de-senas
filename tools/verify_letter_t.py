"""Verifica la T por el camino real de la app (mostrarSena, no applyTestPose).

La T del catalogo era un puno con el pulgar al costado (se leia como A). Ahora
el pulgar se mete bajo el indice y la yema asoma entre indice y medio, con el
mismo cierre de nudillos que la S.
"""
import time
from pathlib import Path

from enfoque_r import MANO, captura, hoja
from mira_t import abrir_nitido, visor_cuadrado
from pose_lab_e import HAND_POS_JS, free_camera, set_cam
from pose_lab_t import MEASURE_JS
from search_t import linea, puntua
from ver_s import CAM_FOV, CAM_ORBIT, CAM_TARGET
import search_e9 as se9

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "verify_t"
OUT.mkdir(parents=True, exist_ok=True)
REF = ROOT / "tools" / "screenshots" / "referencia" / "T_usuario.png"
REF_LAMINA = ROOT / "tools" / "screenshots" / "referencia" / "T.png"

se9.URL = "http://127.0.0.1:8006/practica.html?letra=T&v=tverify"


def cam_app(page):
    page.evaluate(
        """(a) => {
            const mv = document.getElementById('handViewer');
            mv.cameraTarget = a.t;
            mv.cameraOrbit = a.orbit;
            mv.fieldOfView = a.fov;
            mv.jumpCameraToGoal();
        }""",
        {"t": CAM_TARGET, "orbit": CAM_ORBIT, "fov": CAM_FOV},
    )
    time.sleep(0.3)


def main():
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser, page = abrir_nitido(p, lado=760, escala=2)
        visor_cuadrado(page, 700)
        free_camera(page)

        page.evaluate("() => window.__LSM_CONTROLLER__.mostrarSena('T')")
        time.sleep(2.6)

        rotulo = page.inner_text("#anim-info").strip()[:160]
        print("  rotulo:", rotulo)

        cam_app(page)
        m = page.evaluate(MEASURE_JS)
        if m.get("error"):
            print("  medida:", m)
        else:
            print(" ", linea("T catalogo", m, puntua(m)[0]))

        hand = page.evaluate(HAND_POS_JS)
        items = []
        if REF.exists():
            items.append(("REF foto", REF))
        if REF_LAMINA.exists():
            items.append(("REF lamina", REF_LAMINA))

        if hand:
            for vista in ("mano", "lado", "arriba"):
                set_cam(page, vista, hand)
                ruta = OUT / f"T_{vista}.png"
                captura(page, ruta, MANO, margen=0.28, lado=640)
                items.append((f"T {vista}", ruta))

        cam_app(page)
        ruta = OUT / "T_app.png"
        captura(page, ruta, MANO, margen=0.28, lado=640)
        items.append(("T camara app", ruta))

        visor = OUT / "T_visor.png"
        page.query_selector("#handViewer").screenshot(path=str(visor))
        items.append(("T visor", visor))

        browser.close()

    hoja(items, OUT / "_hoja.png", cols=3, cell=420,
         titulo="T verificada · foto, lamina y catalogo")
    print("Capturas en", OUT)


if __name__ == "__main__":
    main()
