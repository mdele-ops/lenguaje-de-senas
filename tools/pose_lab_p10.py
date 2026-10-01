"""P lab 10: ajuste fino a los angulos medidos en la foto del usuario.

Del barrido de eje_p.py: el doblez de la mano DENTRO del plano de la pantalla
se consigue con un extra en el hueso de la muñeca en el eje x, porque `extra`
se aplica despues de `muneca` y por tanto sobre la mano ya puesta de perfil.
Cada grado de ese extra gira el conjunto unos 1.18 grados en pantalla.

Objetivos medidos sobre la foto (rejilla de ref_P_rejilla.png):
    indice ~51, medio ~-2, escuadra ~53

La escuadra de 53 sale bajando el nudillo del medio de 90 a ~55: una mano real
no abre 90 grados entre indice y medio, y eso es parte de por que la version
anterior se veia tiesa.
"""
import itertools
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from pose_lab_e import ARM, BONES
from pose_lab_p7 import CAM_FOV, CAM_ORBIT, CAM_TARGET, hoja
from pose_lab_p9 import MEASURE_JS
import search_e9 as se9
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "lab_p10"
OUT.mkdir(parents=True, exist_ok=True)
FOTO = ROOT / "tools" / "screenshots" / "ref_P_zoom.png"

se9.URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=p10"

WRIST = "mixamorig1RightHand_035"
T1 = "mixamorig1RightHandThumb1_036"
T2 = "mixamorig1RightHandThumb2_037"

OBJ_IDX = 51.0
OBJ_MID = -2.0


def pose_p10(mid_mcp=55, wy=95, ex_x=24, ex_y=0, tcurl=0.85, taside=-0.3,
             t1y=-85, t2x=25, arm_z=-30, idx_spread=4):
    doblez = {"x": ex_x}
    if ex_y:
        doblez["y"] = ex_y
    return {
        "thumb": {"curl": tcurl, "aside": taside},
        "index": {"curl": 0.0, "spread": idx_spread},
        "middle": {"curl": 0.0, "spread": -4},
        "ring": {"curl": 0.95},
        "pinky": {"curl": 0.95},
        "muneca": {"y": wy},
        "extra": {
            WRIST: doblez,
            BONES["middle"][0]: {"x": mid_mcp},
            T1: {"y": t1y},
            T2: {"x": t2x},
            ARM: {"z": arm_z},
        },
    }


def banda(v, lo, hi):
    if v < lo:
        return lo - v
    if v > hi:
        return v - hi
    return 0.0


def puntuar(m):
    p = abs(m["idxAng"] - OBJ_IDX) + 1.2 * abs(m["midAng"] - OBJ_MID)
    p += 60.0 * banda(abs(m["palmNz"]), 0.0, 0.20)   # que siga de perfil
    p += 40.0 * banda(m["midScr"], 0.85, 1.30)       # dedos a su largo
    p += 40.0 * banda(m["idxScr"], 0.72, 1.30)
    p += 0.5 * banda(m["escuadra"], 48.0, 62.0)
    return p


def main():
    rejilla = list(
        itertools.product(
            (48, 55, 62),                 # nudillo del medio -> escuadra
            (90, 95, 100, 105),           # giro de perfil
            (18, 22, 26, 30),             # doblez de la mano en pantalla
            (-10, 0, 10, 20),             # correccion de perfil
        )
    )

    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 1100, "height": 900})
        time.sleep(0.5)
        viewer = page.query_selector("#viewer")
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
        time.sleep(0.4)

        res = []
        for mcp, wy, ex_x, ex_y in rejilla:
            pose = pose_p10(mid_mcp=mcp, wy=wy, ex_x=ex_x, ex_y=ex_y)
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
            m = page.evaluate(MEASURE_JS)
            res.append((puntuar(m), (mcp, wy, ex_x, ex_y), m))
        res.sort(key=lambda t: t[0])

        print(f"{len(rejilla)} combinaciones. Objetivo foto: idx={OBJ_IDX} mid={OBJ_MID}")
        for s, k, m in res[:12]:
            print(
                f"  mcp{k[0]:<3} wy{k[1]:<4} ex{k[2]:<3} ey{k[3]:<4} score={s:6.2f} "
                f"idx={m['idxAng']:+6.1f} mid={m['midAng']:+6.1f} "
                f"esc={m['escuadra']:5.1f} palmNz={m['palmNz']:+.2f} "
                f"scr={m['idxScr']:.2f}/{m['midScr']:.2f} mano={m['manoAng']:+6.1f}"
            )

        items = [("REF foto", FOTO)] if FOTO.exists() else []
        elegidos = {}
        for s, k, m in res[:8]:
            elegidos[f"mcp{k[0]}_wy{k[1]}_ex{k[2]}_ey{k[3]}"] = pose_p10(
                mid_mcp=k[0], wy=k[1], ex_x=k[2], ex_y=k[3]
            )
        for name, pose in elegidos.items():
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
            time.sleep(0.3)
            path = OUT / f"{name}.png"
            viewer.screenshot(path=str(path))
            items.append((name, path))

        browser.close()

    hoja(items, OUT / "_produccion.png", cols=3, cell=340, caja=(215, 70, 435, 290))
    (OUT / "_casos.json").write_text(json.dumps(elegidos, indent=2), "utf-8")


if __name__ == "__main__":
    main()
