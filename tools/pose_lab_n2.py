"""N lab 2: dos lomos (indice y medio) sobre el pulgar, anular y menique
cerrados, yema del pulgar entre medio y anular.

La N del catalogo es un puno generico (curl 0.85 en los cinco). En la lamina
el pulgar cruza por debajo y asoma ENTRE medio y anular; indice y medio se
doblan juntos encima (dos lomos); anular y menique van cerrados a un lado.
La muneca, si se mueve, es una flexion ligera para que los nudillos miren
a la camara — no la caida de 150 deg de la M colgante.
"""
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from pose_lab_e import ARM, BONES, HAND_POS_JS, T1, T2, T3, free_camera, set_cam
from pose_lab_m5 import hoja
from pose_lab_m6 import pose_curl
from pulgar_e import PULGAR_JS
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "lab_n2"
OUT.mkdir(parents=True, exist_ok=True)
REF = ROOT / "tools" / "screenshots" / "referencia" / "N_usuario.png"

import search_e9 as se9

se9.URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=n2"

I1, I2, I3 = BONES["index"][:3]
M1, M2, M3 = BONES["middle"][:3]
R1, R2, R3 = BONES["ring"][:3]
P1, P2, P3 = BONES["pinky"][:3]

# Lomos de indice/medio (de la M B_eq72) + anular/menique cerrados.
LOMOS2 = {
    I1: {"x": 8.6},
    I2: {"x": 13},
    I3: {"x": -12},
    M1: {"x": 4.9},
    M2: {"x": 11.5},
    M3: {"x": -1},
    R1: {"x": 8},
    R2: {"x": 16},
    R3: {"x": 20},
    P1: {"x": 8},
    P2: {"x": 16},
    P3: {"x": 20},
}

# PIP mas marcado: en la foto el nudillo MCP queda arriba y el pliegue
# visible es la falange media, no un puno redondo.
PIP_ALTO = dict(LOMOS2)
PIP_ALTO[I2] = {"x": 22}
PIP_ALTO[M2] = {"x": 20}
PIP_ALTO[I1] = {"x": 2}
PIP_ALTO[M1] = {"x": -2}

THUMB_M = dict(tcurl=0.48, taside=0.18, t1={"x": 16, "y": -60, "z": 48}, t2x=28, t3x=18)
THUMB_CORTO = dict(
    tcurl=0.52, taside=0.10, t1={"x": 14, "y": -55, "z": 32}, t2x=22, t3x=12
)
THUMB_MEDIO = dict(
    tcurl=0.50, taside=0.14, t1={"x": 16, "y": -58, "z": 38}, t2x=24, t3x=14
)

SPREAD_N = (-6, 2, 8, 16)


def n_pose(thumb, more, mx=0, my=0, mz=0, ic=0.88, mc=0.88, rc=1.0, pc=1.0, spread=SPREAD_N):
    data = pose_curl(ic, mc, rc, pc, spread, more=more, **thumb)
    muneca = {k: v for k, v in (("x", mx), ("y", my), ("z", mz)) if v}
    if muneca:
        data["muneca"] = muneca
    return data


CAT = json.loads((ROOT / "data" / "catalogo-lsm.json").read_text("utf-8"))
CASES = {
    "00_actual": next(s for s in CAT["senas"] if s["letra"] == "N")["pose"],
    "A_lomos_Mthumb": n_pose(THUMB_M, LOMOS2),
    "B_corto": n_pose(THUMB_CORTO, LOMOS2),
    "C_medio": n_pose(THUMB_MEDIO, LOMOS2),
    "D_pip": n_pose(THUMB_MEDIO, PIP_ALTO),
    "E_x18": n_pose(THUMB_MEDIO, LOMOS2, mx=18),
    "F_x32": n_pose(THUMB_MEDIO, LOMOS2, mx=32),
    "G_x48": n_pose(THUMB_MEDIO, PIP_ALTO, mx=28),
    "H_y12": n_pose(THUMB_MEDIO, LOMOS2, my=12),
    "I_x28_y8": n_pose(THUMB_MEDIO, PIP_ALTO, mx=28, my=8),
    "J_curl82": n_pose(THUMB_MEDIO, PIP_ALTO, mx=22, ic=0.82, mc=0.82),
}


def main():
    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 900, "height": 950})
        time.sleep(0.3)
        viewer = page.query_selector("#viewer")
        free_camera(page)

        frente, lado, prod = [], [], []
        if REF.exists():
            frente.append(("REF foto", REF))
            lado.append(("REF foto", REF))

        for name, data in CASES.items():
            page.evaluate(
                "(pose) => window.__LSM_CONTROLLER__.applyTestPose(pose)", data
            )
            time.sleep(0.32)
            t = page.evaluate(PULGAR_JS)
            print(
                f"{name:16s} across={t['across4']:+.2f} frente={t['frente4']:+.2f} "
                f"alto={t['alto4']:+.2f} frenteMax={t['frenteMax']:+.2f}"
            )
            hand = page.evaluate(HAND_POS_JS)
            set_cam(page, "mano", hand)
            p_f = OUT / f"{name}_frente.png"
            viewer.screenshot(path=str(p_f))
            frente.append((name, p_f))

            set_cam(page, "lado", hand)
            p_l = OUT / f"{name}_lado.png"
            viewer.screenshot(path=str(p_l))
            lado.append((name, p_l))

            set_cam(page, "prod", hand)
            p_p = OUT / f"{name}_prod.png"
            viewer.screenshot(path=str(p_p))
            prod.append((name, p_p))

        browser.close()

    hoja(frente, OUT / "_frente.png", cols=4, cell=280)
    hoja(lado, OUT / "_lado.png", cols=4, cell=280)
    hoja(prod, OUT / "_prod.png", cols=4, cell=280)


if __name__ == "__main__":
    main()
