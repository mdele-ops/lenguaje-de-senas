"""Verifica la C final por el camino de produccion: catalogo embebido + mostrarSena.

No intercepta nada: carga practica.html tal cual y pulsa la letra como un usuario,
para confirmar que lo que quedo en js/catalogo-lsm.js es lo que se ve.
"""
import time
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

import c_lab
import lab

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "tools" / "screenshots" / "ref_c" / "ref_c_original.png"
OUT = ROOT / "tools" / "screenshots" / "verify_c"
URL = "http://localhost:8123/practica.html?letra=C&v=cfinal"

VISTAS = {
    "app_frontal": ("0m 2.45m 0.15m", "0deg 84deg 2.5m", "30deg"),
}


def square(path):
    img = Image.open(path)
    s = min(img.size)
    img.crop(((img.width - s) // 2, 0, (img.width - s) // 2 + s, s)).save(path)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = c_lab.launch(p)
        page = browser.new_page(viewport={"width": 900, "height": 900})
        page.goto(URL, wait_until="networkidle", timeout=60000)
        page.wait_for_selector("#anim-info", timeout=30000, state="attached")
        if not lab.poll_ready(page):
            raise RuntimeError("El modelo 3D no cargo")
        time.sleep(1.5)

        pose = page.evaluate("() => window.__LSM_CONTROLLER__.getSena('C').pose")
        print("pose C servida por el catalogo embebido:")
        print(" muneca:", pose.get("muneca"))
        print(" thumb :", pose.get("thumb"))
        print(" index :", pose.get("index"))

        # Camino de produccion, con la transicion de 2 s.
        page.evaluate("() => window.__LSM_CONTROLLER__.mostrarSena('C')")
        time.sleep(3.0)
        print("estado:", page.inner_text("#anim-info").strip()[:120])

        viewer = page.query_selector("#viewer")
        shots = []
        for name, (target, orbit, fov) in VISTAS.items():
            page.evaluate(
                """(a) => {
                    const mv = document.getElementById('handViewer');
                    mv.cameraTarget = a.t;
                    mv.cameraOrbit = a.o;
                    mv.fieldOfView = a.f;
                    mv.jumpCameraToGoal();
                }""",
                {"t": target, "o": orbit, "f": fov},
            )
            time.sleep(0.5)
            out = OUT / f"{name}.png"
            viewer.screenshot(path=str(out))
            square(out)
            shots.append((name, out))
            print("  captura", name, flush=True)

        # Primer plano encuadrado sobre la mano, para comparar con la foto.
        near = OUT / "primer_plano.png"
        lab.shot(page, near, orbit="0deg 84deg 0.32m", side="right")
        shots.append(("primer_plano", near))

        unit = c_lab.scales(page)
        page.evaluate("() => window.__LSM_CONTROLLER__.mostrarSena('C')")
        time.sleep(3.0)
        print("metricas finales:", c_lab.metrics(page, unit))

        browser.close()

    lab.sheet([("REFERENCIA", REF)] + shots, OUT / "_vs_referencia.png", cols=3, cell=340)


if __name__ == "__main__":
    main()
