"""T: candidatas contra la foto del usuario.

La T del catalogo es un puno con el pulgar al costado (se lee como A). En la
lamina el pulgar se mete BAJO el indice y la yema asoma entre indice y medio.
Se comparan la pose actual, la del laboratorio (pulgar en la muesca) y esa
misma con el puno cerrado de la S (flexion extra en los nudillos).
"""
import json
import time
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

from enfoque_r import MANO, captura, hoja
from pose_lab_e import T1, T2, T3, free_camera
from pose_lab_t import MEASURE_JS, pose_t
from puno_s import flexion
from search_t import construye, linea, puntua
from ver_s import CAM_FOV, CAM_ORBIT, CAM_TARGET
import search_e9 as se9
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "elige_t"
OUT.mkdir(parents=True, exist_ok=True)
REF = ROOT / "tools" / "screenshots" / "referencia" / "T_usuario.png"
AFINADA = ROOT / "tools" / "screenshots" / "afina_t" / "_afinada.json"

se9.URL = "http://127.0.0.1:8006/practica.html?letra=%E2%97%8B&v=eligeT"

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
    time.sleep(0.28)


def con_puno(receta):
    """La receta del lab, con el mismo cierre de nudillos que la S."""
    pose = construye(receta)
    pose["index"]["curl"] = 0.9
    pose["middle"]["curl"] = 0.9
    pose["ring"]["curl"] = 0.9
    pose["pinky"]["curl"] = 0.9
    pose["extra"].update(flexion(prox=30))
    return pose


def ref_grande(lado=560):
    im = Image.open(REF).convert("RGB")
    # recorte de la mano, sin el banner Tt
    w, h = im.size
    mano = im.crop((int(w * 0.12), int(h * 0.04), int(w * 0.88), int(h * 0.78)))
    ruta = OUT / "_ref.png"
    mano.resize((lado, lado), Image.LANCZOS).save(ruta)
    return ruta


def main():
    catalogo = json.loads((ROOT / "data" / "catalogo-lsm.json").read_text("utf-8"))
    por_letra = {s["letra"]: s for s in catalogo["senas"]}

    r_ap = dict(RECETA, sep=10)
    r_cerr = dict(RECETA, sep=8, tcurl=0.4)

    casos = {
        "0_catalogo": por_letra["T"]["pose"],
        "1_lab": construye(RECETA),
        "2_lab_puno": con_puno(RECETA),
        "3_puno_sep10": con_puno(r_ap),
        "4_puno_sep8": con_puno(r_cerr),
        "S_catalogo": por_letra["S"]["pose"],
        "A_catalogo": por_letra["A"]["pose"],
    }

    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 900, "height": 900})
        time.sleep(0.3)
        free_camera(page)
        cam(page)

        items = [("REF foto", ref_grande())]
        medidas = {}
        for nombre, pose in casos.items():
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
            time.sleep(0.35)
            cam(page)
            m = page.evaluate(MEASURE_JS)
            medidas[nombre] = m
            if not m.get("error") and nombre[0] in "01234":
                print(" ", linea(nombre, m, puntua(m)[0]))
            for vista, orbit in (
                ("frente", "0deg 84deg 2.5m"),
                ("tres_cuartos", "-35deg 84deg 2.5m"),
            ):
                cam(page, orbit)
                ruta = OUT / f"{nombre}_{vista}.png"
                captura(page, ruta, MANO, margen=0.24, lado=560)
                items.append((f"{nombre} {vista}", ruta))

        browser.close()

    hoja(items, OUT / "_hoja.png", cols=4, cell=400,
         titulo="T · foto vs catalogo vs laboratorio vs puno cerrado")
    (OUT / "_casos.json").write_text(
        json.dumps({k: v for k, v in casos.items()}, indent=2), "utf-8"
    )
    print("Capturas en", OUT)


if __name__ == "__main__":
    main()
