"""P lab 5: que el pulgar asome en el hueco, como en la lamina.

En la K del catalogo el pulgar queda escondido detras del puno y no se ve; en
la lamina de la P es un boton claro entre el indice y el medio, y es lo que
distingue la letra de una simple "escuadra" de dos dedos. Aqui se prueban
variantes desde el pulgar estirado hacia arriba hasta el recogido, y se miran
en la vista de produccion (de frente) y de perfil.
"""
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from pose_lab_e import ARM, BONES, HAND_POS_JS, T1, T2, T3, free_camera
from pose_lab_p import REF
from pose_lab_p3 import hoja_comparativa
from pose_lab_p4 import MEASURE_JS
import search_e9 as se9
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "lab_p5"
OUT.mkdir(parents=True, exist_ok=True)

se9.URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=p5"

VIEWS = {
    "prod": ("0deg 84deg 1.40m", "21deg", 0.04),
    "perfil": ("-88deg 84deg 0.62m", "26deg", 0.02),
}

WRIST = {"y": 45, "z": 12}


def pose_p5(tcurl, taside, t1=None, t2x=0, t3x=0, mid_mcp=90, wrist=None):
    ex = {ARM: {"z": -18}, BONES["middle"][0]: {"x": mid_mcp}}
    if t1:
        ex[T1] = dict(t1)
    if t2x:
        ex[T2] = {"x": t2x}
    if t3x:
        ex[T3] = {"x": t3x}
    return {
        "thumb": {"curl": tcurl, "aside": taside},
        "index": {"curl": 0.0, "spread": 4},
        "middle": {"curl": 0.0, "spread": -4},
        "ring": {"curl": 0.95},
        "pinky": {"curl": 0.95},
        "muneca": dict(wrist or WRIST),
        "extra": ex,
    }


CASES = {
    "00_p4": pose_p5(0.25, 0.0, t1={"y": -40}, t2x=20),
    # pulgar estirado hacia arriba, pegado al indice
    "A_recto": pose_p5(0.0, 0.0),
    "B_recto_sep": pose_p5(0.0, 0.25),
    "C_recto_z": pose_p5(0.0, 0.1, t1={"z": -25}),
    # inclinado hacia el medio, cruzando el hueco
    "D_cruza": pose_p5(0.15, 0.15, t1={"y": -30, "z": -20}),
    "E_cruza2": pose_p5(0.15, 0.3, t1={"y": -45, "z": -30}),
    "F_cruza3": pose_p5(0.3, 0.15, t1={"y": -30, "z": -30}, t2x=25),
    # solo la yema doblada, la base recta (el boton de la lamina)
    "G_yema": pose_p5(0.0, 0.15, t2x=45),
    "H_yema2": pose_p5(0.0, 0.15, t2x=45, t3x=30),
    "I_yema3": pose_p5(0.0, 0.3, t1={"z": -18}, t2x=55, t3x=25),
    "J_yema4": pose_p5(0.1, 0.2, t1={"y": -20, "z": -15}, t2x=50, t3x=20),
}


def main():
    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 900, "height": 900})
        time.sleep(0.3)
        viewer = page.query_selector("#viewer")
        free_camera(page)

        hojas = {k: ([("REF lamina", REF)] if REF.exists() else []) for k in VIEWS}
        for name, pose in CASES.items():
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
            time.sleep(0.3)
            m = page.evaluate(MEASURE_JS)
            print(
                f"{name:10s} tPip={m['tPip']:.2f} tIdx={m['tIdxProx']:.2f} "
                f"tOut={m['tOut']:.2f} tRise={m['tRise']:+.2f} tLen={m['tLen']:.2f}"
            )
            hand = page.evaluate(HAND_POS_JS)
            for view, (orbit, fov, dy) in VIEWS.items():
                page.evaluate(
                    """(a) => {
                        const mv = document.getElementById('handViewer');
                        mv.cameraTarget = a.t;
                        mv.cameraOrbit = a.orbit;
                        mv.fieldOfView = a.fov;
                        mv.jumpCameraToGoal();
                    }""",
                    {
                        "t": "%.3fm %.3fm %.3fm"
                        % (hand["x"], hand["y"] + dy, hand["z"]),
                        "orbit": orbit,
                        "fov": fov,
                    },
                )
                time.sleep(0.15)
                path = OUT / f"{name}_{view}.png"
                viewer.screenshot(path=str(path))
                hojas[view].append((name, path))

        browser.close()

    for view, items in hojas.items():
        hoja_comparativa(items, OUT / f"_{view}.png", cols=4, cell=320)
    (OUT / "_casos.json").write_text(json.dumps(CASES, indent=2), "utf-8")


if __name__ == "__main__":
    main()
