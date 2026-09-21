"""T: mirar las finalistas de la rejilla al lado de la lamina.

La puntuacion de `search_t.py` dice que el pulgar cae en el hueco y asoma, pero
no dice si la mano se lee como una T: eso hay que verlo. Se sacan las mejores
en tres vistas, con el mismo recorte que la lamina, para poder compararlas.

La vista que decide es "frente" (es la de la app); "arriba" enseña si el pulgar
esta metido entre los dedos o solo apoyado delante, que a 0 grados engaña.
"""
import json
import time
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

from enfoque_r import MANO, captura, hoja
from pose_lab_e import free_camera
from pose_lab_t import MEASURE_JS
from search_t import construye, linea, puntua
from ver_s import CAM_FOV, CAM_TARGET
import search_e9 as se9
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "ver_t"
OUT.mkdir(parents=True, exist_ok=True)
TOP = ROOT / "tools" / "screenshots" / "search_t" / "_top.json"
LAMINA = ROOT / "tools" / "screenshots" / "lamina_T.png"

se9.URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=t3"

VISTAS = (("frente", "0deg 84deg 2.5m"),
          ("tres_cuartos", "-40deg 84deg 2.5m"),
          ("arriba", "0deg 45deg 2.5m"))

CUANTAS = 8


def ref_grande(lado=520):
    """La lamina recortada a la mano, al mismo tamano que los renders."""
    im = Image.open(LAMINA).convert("RGB").crop((46, 30, 152, 168))
    ruta = OUT / "_ref.png"
    im.resize((lado, lado), Image.LANCZOS).save(ruta)
    return ruta


def cam(page, orbit):
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
    time.sleep(0.22)


def nombre_de(r):
    return "_".join(f"{k}{v}" for k, v in r.items())


def main():
    top = json.loads(TOP.read_text("utf-8"))[:CUANTAS]

    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 1100, "height": 1100})
        time.sleep(0.4)
        free_camera(page)

        items = [("REF lamina", ref_grande())]
        elegidas = {}
        for i, cand in enumerate(top):
            r = cand["receta"]
            nombre = f"{i:02d}_" + nombre_de(r)
            pose = construye(r)
            elegidas[nombre] = {"receta": r, "pose": pose}
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
            time.sleep(0.3)
            cam(page, VISTAS[0][1])
            m = page.evaluate(MEASURE_JS)
            print(" ", linea(nombre, m, puntua(m)[0]))
            for vista, orbit in VISTAS:
                cam(page, orbit)
                ruta = OUT / f"{nombre}_{vista}.png"
                captura(page, ruta, MANO, margen=0.28, lado=520)
                items.append((f"{i:02d} {vista}", ruta))

        browser.close()

    hoja(items, OUT / "_hoja.png", cols=5, cell=340, titulo="T · finalistas rejilla 1")
    (OUT / "_elegidas.json").write_text(json.dumps(elegidas, indent=2), "utf-8")
    print("Capturas en", OUT)


if __name__ == "__main__":
    main()
