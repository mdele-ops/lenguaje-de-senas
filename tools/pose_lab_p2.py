"""P lab 2: pulgar entre indice y medio, y giro de muneca legible de frente.

La forma quedo resuelta en pose_lab_p (indice recto arriba + nudillo del medio
a ~90). Faltan dos cosas:

  - el pulgar. En la foto asoma como un boton rosado entre el indice y el
    medio; con el pulgar recogido de la K se pierde detras del puno.
  - el giro. La lamina esta de perfil, pero la practica se ve de frente: si el
    medio apunta justo a la camara se ve como un muñon. Hay que girar la
    muneca lo justo para que el medio se lea en escorzo sin dejar de ser la P.
"""
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from pose_lab_e import HAND_POS_JS, free_camera
from pose_lab_m5 import hoja
from pose_lab_p import MEASURE_JS, OUT as OUT_P, REF, pose_p
import search_e9 as se9
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "lab_p2"
OUT.mkdir(parents=True, exist_ok=True)

se9.URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=p2"

VIEWS = {
    # lo que ve el usuario en practica.html, pero acercado con teleobjetivo:
    # de cerca la camara se mete dentro del brazo izquierdo del avatar
    "prod": (None, "0deg 84deg 1.60m", "11deg"),
    "perfil": (None, "-88deg 84deg 0.60m", "26deg"),
    "tresc": (None, "-40deg 84deg 0.60m", "26deg"),
}


def set_cam(page, kind, hand):
    t, orbit, fov = VIEWS[kind]
    if t is None:
        t = "%.3fm %.3fm %.3fm" % (hand["x"], hand["y"], hand["z"])
    page.evaluate(
        """(a) => {
            const mv = document.getElementById('handViewer');
            mv.cameraTarget = a.t;
            mv.cameraOrbit = a.orbit;
            mv.fieldOfView = a.fov;
            mv.jumpCameraToGoal();
        }""",
        {"t": t, "orbit": orbit, "fov": fov},
    )
    time.sleep(0.12)


BASE = dict(mid_mcp=90, spread=(4, -4))

CASES = {
    "A_base": pose_p(**BASE),
    # --- pulgar: que la yema asome entre indice y medio -------------------
    "B_t_up": pose_p(**BASE, tcurl=0.0, taside=0.35),
    "C_t_up2": pose_p(**BASE, tcurl=0.15, taside=0.45, t1={"y": -25}),
    "D_t_ext": pose_p(**BASE, tcurl=0.1, taside=0.25, t1={"y": -35, "z": -10}),
    "E_t_K": pose_p(**BASE, tcurl=0.3, taside=0.3, t2x=-20),
    "F_t_recto": pose_p(**BASE, tcurl=0.2, taside=0.4, t1={"y": -15}, t2x=-25),
    # --- giro de muneca: legibilidad de frente -----------------------------
    "G_wy-20": pose_p(**BASE, tcurl=0.15, taside=0.45, t1={"y": -25}, wrist={"y": -20}),
    "H_wy-35": pose_p(**BASE, tcurl=0.15, taside=0.45, t1={"y": -25}, wrist={"y": -35}),
    "I_wy-50": pose_p(**BASE, tcurl=0.15, taside=0.45, t1={"y": -25}, wrist={"y": -50}),
    "J_wy25": pose_p(**BASE, tcurl=0.15, taside=0.45, t1={"y": -25}, wrist={"y": 25}),
    "K_wy40": pose_p(**BASE, tcurl=0.15, taside=0.45, t1={"y": -25}, wrist={"y": 40}),
    "L_wy55": pose_p(**BASE, tcurl=0.15, taside=0.45, t1={"y": -25}, wrist={"y": 55}),
    # --- inclinacion del conjunto -----------------------------------------
    "M_wy40_x10": pose_p(
        **BASE, tcurl=0.15, taside=0.45, t1={"y": -25}, wrist={"y": 40, "x": 10}
    ),
    "N_wy40_z20": pose_p(
        **BASE, tcurl=0.15, taside=0.45, t1={"y": -25}, wrist={"y": 40, "z": 20}
    ),
}


def main():
    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 900, "height": 950})
        time.sleep(0.3)
        viewer = page.query_selector("#viewer")
        free_camera(page)

        hojas = {k: [] for k in VIEWS}
        if REF.exists():
            for k in hojas:
                hojas[k].append(("REF lamina", REF))

        for name, data in CASES.items():
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", data)
            time.sleep(0.3)
            m = page.evaluate(MEASURE_JS)
            print(
                f"{name:12s} idxUp={m['idxUp']:+.2f} midFwd={m['midFwd']:+.2f} "
                f"midUp={m['midUp']:+.2f} midSide={m['midSide']:+.2f} "
                f"ang={m['escuadra']:5.1f} tIdx={m['thumbIdx']:.2f} "
                f"tMid={m['thumbMid']:.2f} tY={m['thumbTipY']:+.2f}"
            )
            hand = page.evaluate(HAND_POS_JS)
            for view in VIEWS:
                set_cam(page, view, hand)
                path = OUT / f"{name}_{view}.png"
                viewer.screenshot(path=str(path))
                hojas[view].append((name, path))

        browser.close()

    for view, items in hojas.items():
        hoja(items, OUT / f"_{view}.png", cols=4, cell=300)
    (OUT / "_casos.json").write_text(json.dumps(CASES, indent=2), "utf-8")


if __name__ == "__main__":
    main()
