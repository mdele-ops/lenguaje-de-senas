"""S lab 9: finalistas del pulgar, grandes y al lado de la lamina.

Las hojas de contacto de los barridos sirven para descartar, pero a 300 px no
se ve si la yema del pulgar apoya sobre los dedos o se queda flotando. Aqui se
sacan solo las finalistas, a 560 px y con la lamina en la misma hoja.
"""
import json
import time
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

from enfoque_r import MANO, captura, hoja
from pose_lab_e import T1, T2, T3, free_camera
from pose_lab_s import MEASURE_JS
from search_s2 import puno_s
from search_s6 import linea
from ver_s import VISTAS, cam
import search_e9 as se9
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "final_s"
OUT.mkdir(parents=True, exist_ok=True)
LAMINA = ROOT / "tools" / "screenshots" / "lamina_S.png"

se9.URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=s9"


def pulgar(tc, z, y, x, t2x, t2y):
    return puno_s(
        tcurl=tc, thumb={T1: {"x": x, "y": y, "z": z}, T2: {"x": t2x, "y": t2y}}
    )


# Las tres que salen del lab 14 con hueco suficiente (gap >= 0.17) para que la
# malla del pulgar no se meta en la de los dedos.
FINALISTAS = {
    "A_tumbado": pulgar(0.4, 0, -75, 20, 45, -25),
    "B_medio": pulgar(0.3, 0, -95, 30, 45, -25),
    "C_alto": pulgar(0.3, 10, -95, 40, 45, -25),
}


def ref_grande(lado=560):
    """La lamina recortada a la mano y llevada al mismo tamano que los renders."""
    im = Image.open(LAMINA).convert("RGB").crop((10, 4, 74, 76))
    ruta = OUT / "_ref.png"
    im.resize((lado, lado), Image.LANCZOS).save(ruta)
    return ruta


def main():
    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 1100, "height": 1100})
        time.sleep(0.4)
        free_camera(page)
        cam(page, "0deg 84deg 2.5m")

        items = [("REF lamina", ref_grande())]
        for nombre, pose in FINALISTAS.items():
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
            time.sleep(0.32)
            cam(page, "0deg 84deg 2.5m")
            print(" ", linea(nombre, page.evaluate(MEASURE_JS)))
            for vista, orbit in VISTAS:
                ruta = OUT / f"{nombre}_{vista}.png"
                cam(page, orbit)
                captura(page, ruta, MANO, margen=0.26, lado=560)
                items.append((f"{nombre} {vista}", ruta))

        browser.close()

    hoja(items, OUT / "_hoja.png", cols=4, cell=430, titulo="S · finalistas")
    (OUT / "_poses.json").write_text(json.dumps(FINALISTAS, indent=2), "utf-8")
    print("Capturas en", OUT)


if __name__ == "__main__":
    main()
