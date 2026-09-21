"""T: capturas nitidas de las dos finalistas contra la foto."""
import json
import time
from pathlib import Path

from enfoque_r import MANO, captura, hoja
from mira_t import abrir_nitido, visor_cuadrado
from pose_lab_e import free_camera
from puno_s import flexion
from search_t import construye
from ver_s import CAM_FOV, CAM_ORBIT, CAM_TARGET
import search_e9 as se9

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "elige_t"
REF = ROOT / "tools" / "screenshots" / "elige_t" / "_ref.png"
AFINADA = ROOT / "tools" / "screenshots" / "afina_t" / "_afinada.json"

se9.URL = "http://127.0.0.1:8006/practica.html?letra=%E2%97%8B&v=eligeT2"

RECETA = json.loads(AFINADA.read_text("utf-8"))["receta"]


def cam(page, orbit=CAM_ORBIT):
    page.evaluate(
        """(a) => {
            const mv = document.getElementById('handViewer');
            mv.cameraTarget = a.t;
            mv.cameraOrbit = a.orbit;
            mv.fieldOfView = a.fov;
            mv.jumpCameraToGoal();
        }""",
        {"t": CAM_TARGET, "orbit": orbit, "fov": CAM_FOV},
    )
    time.sleep(0.35)


def con_puno(receta):
    pose = construye(receta)
    for d in ("index", "middle", "ring", "pinky"):
        pose[d]["curl"] = 0.9
    pose["extra"].update(flexion(prox=30))
    return pose


def main():
    catalogo = json.loads((ROOT / "data" / "catalogo-lsm.json").read_text("utf-8"))
    por_letra = {s["letra"]: s for s in catalogo["senas"]}
    receta_sep10 = dict(RECETA, sep=10)

    casos = {
        "catalogo": por_letra["T"]["pose"],
        "lab_puno": con_puno(RECETA),
        "puno_sep10": con_puno(receta_sep10),
        "S": por_letra["S"]["pose"],
        "A": por_letra["A"]["pose"],
    }

    with sync_playwright_open() as (browser, page):
        visor_cuadrado(page, 700)
        free_camera(page)
        cam(page)

        items = [("REF foto", REF)] if REF.exists() else []
        for nombre, pose in casos.items():
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
            time.sleep(0.4)
            for vista, orbit in (
                ("frente", "0deg 84deg 2.5m"),
                ("tres_cuartos", "-40deg 84deg 2.5m"),
                ("dorso", "0deg 70deg 2.5m"),
            ):
                cam(page, orbit)
                ruta = OUT / f"nitido_{nombre}_{vista}.png"
                captura(page, ruta, MANO, margen=0.32, lado=640)
                items.append((f"{nombre} {vista}", ruta))
            entero = OUT / f"nitido_{nombre}_visor.png"
            page.query_selector("#handViewer").screenshot(path=str(entero))
            items.append((f"{nombre} visor", entero))

        browser.close()

    hoja(items, OUT / "_nitido.png", cols=4, cell=420,
         titulo="T nitida · catalogo vs lab+puno vs S/A")
    print("Capturas en", OUT)


def sync_playwright_open():
    from playwright.sync_api import sync_playwright
    class Ctx:
        def __enter__(self):
            self.p = sync_playwright().start()
            self.browser, self.page = abrir_nitido(self.p, lado=760, escala=2)
            return self.browser, self.page
        def __exit__(self, *a):
            self.p.stop()
    return Ctx()


if __name__ == "__main__":
    main()
