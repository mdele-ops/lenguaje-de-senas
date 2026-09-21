"""T: la pose afinada, en grande y al lado de sus vecinas.

Los numeros de `afina_t.py` estan en cero, pero eso solo dice que la yema cae
donde la lamina manda. Falta lo que ningun numero cubre: que la mano se LEA
como una T y no se confunda con la A ni con la S, que son el mismo puno.

Se pinta la lamina, la T afinada (de frente, de tres cuartos y desde arriba,
con y sin esqueleto) y al lado la A y la S del catalogo en la vista de la app.
"""
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from enfoque_r import hoja
from mira_t import abrir_nitido, captura
from pose_lab_e import free_camera
from pose_lab_t import MEASURE_JS
from search_t import construye, linea, puntua
from ver_s import CAM_FOV, CAM_TARGET
from ver_t import ref_grande

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "revisa_t"
OUT.mkdir(parents=True, exist_ok=True)
AFINADA = ROOT / "tools" / "screenshots" / "afina_t" / "_afinada.json"

import search_e9 as se9
se9.URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=t9"

VISTAS = (("frente", "0deg 84deg 2.5m"),
          ("tres_cuartos", "-35deg 84deg 2.5m"),
          ("arriba", "0deg 48deg 2.5m"))


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


def main():
    catalogo = json.loads((ROOT / "data" / "catalogo-lsm.json").read_text("utf-8"))
    por_letra = {s["letra"]: s for s in catalogo["senas"]}
    receta = json.loads(AFINADA.read_text("utf-8"))["receta"]
    pose_t = construye(receta)

    with sync_playwright() as p:
        browser, page = abrir_nitido(p, lado=760, escala=2)
        free_camera(page)

        items = [("REF lamina", ref_grande(700))]

        page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose_t)
        time.sleep(0.35)
        cam(page, VISTAS[0][1])
        m = page.evaluate(MEASURE_JS)
        print(" ", linea("T afinada", m, puntua(m)[0]))
        for vista, orbit in VISTAS:
            cam(page, orbit)
            for sufijo, esq in (("", False), ("_esq", True)):
                ruta = OUT / f"T_{vista}{sufijo}.png"
                captura(page, ruta, esqueleto=esq, margen=0.24, lado=700)
                items.append((f"T {vista}{sufijo}", ruta))

        # las vecinas, solo de frente: es donde se tienen que distinguir
        for letra in ("A", "S", "E"):
            page.evaluate(
                "(x) => window.__LSM_CONTROLLER__.applyTestPose(x)",
                por_letra[letra]["pose"],
            )
            time.sleep(0.35)
            cam(page, VISTAS[0][1])
            ruta = OUT / f"{letra}_frente.png"
            captura(page, ruta, esqueleto=False, margen=0.24, lado=700)
            items.append((f"{letra} (catalogo)", ruta))

        browser.close()

    hoja(items, OUT / "_hoja.png", cols=4, cell=440,
         titulo="T afinada · contra la lamina y contra A / S / E")
    (OUT / "_pose.json").write_text(json.dumps(pose_t, indent=2), "utf-8")
    print("Capturas en", OUT)


if __name__ == "__main__":
    main()
