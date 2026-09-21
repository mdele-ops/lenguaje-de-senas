"""M lab 7: iguala los tres lomos y cierra un poco mas, partiendo de A_curl88."""
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from pose_lab_e import BONES, HAND_POS_JS, free_camera, set_cam
from pose_lab_m5 import MEASURE_JS, hoja
from pose_lab_m6 import T1_C, pose_curl
from pulgar_e import PULGAR_JS
from search_e9 import abrir
from simetria_e import SIMETRIA_JS, detalle, informe

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "lab_m7"
OUT.mkdir(parents=True, exist_ok=True)
REF = ROOT / "tools" / "screenshots" / "referencia" / "M_usuario.png"

import search_e9 as se9

se9.URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=m7"

I1, I2, I3 = BONES["index"][:3]
M1, M2, M3 = BONES["middle"][:3]
R1, R2, R3 = BONES["ring"][:3]
P1, P2, P3 = BONES["pinky"][:3]

# Extra de A_curl88 (PIP_LOMO) + correccion para igualar angulos medidos:
#   mcp 63.4/67.1/75.1 -> 72
#   pip 96.9/98.5/93.8 -> 98
#   dip 67.2/56.2/40.1 -> 55
EQ3 = {
    I1: {"x": 8.6},
    I2: {"x": 13},
    I3: {"x": -12},
    M1: {"x": 4.9},
    M2: {"x": 11.5},
    M3: {"x": -1},
    R1: {"x": -3.1},
    R2: {"x": 16.2},
    R3: {"x": 15},
    P1: {"x": 8},
    P2: {"x": 16},
    P3: {"x": 20},
}

# Un poco mas de MCP para que el lomo se vea de frente (objetivo ~78).
SQ = dict(EQ3)
SQ[I1] = {"x": 14.6}
SQ[M1] = {"x": 10.9}
SQ[R1] = {"x": 2.9}

SPREAD = (-8, -2, 4, 14)
THUMB = dict(tcurl=0.48, taside=0.18, t1=T1_C, t2x=28, t3x=18)

CAT = json.loads((ROOT / "data" / "catalogo-lsm.json").read_text("utf-8"))
CASES = {
    "00_actual": next(s for s in CAT["senas"] if s["letra"] == "M")["pose"],
    "A_curl88": pose_curl(
        0.88, 0.88, 0.88, 1.0, SPREAD,
        more={
            I2: {"x": 12}, M2: {"x": 12}, R2: {"x": 12},
            P1: {"x": 8}, P2: {"x": 16}, P3: {"x": 20},
        },
        **THUMB,
    ),
    "B_eq72": pose_curl(0.88, 0.88, 0.88, 1.0, SPREAD, more=EQ3, **THUMB),
    "C_sq78": pose_curl(0.88, 0.88, 0.88, 1.0, SPREAD, more=SQ, **THUMB),
    "D_eq_arm0": pose_curl(
        0.88, 0.88, 0.88, 1.0, SPREAD, more=EQ3, **THUMB
    ),
    "E_eq_juntar": pose_curl(
        0.88, 0.88, 0.88, 1.0, (-11, -3, 5, 16), more=EQ3, **THUMB
    ),
}


def main():
    # D: sin el giro del brazo de la E
    CASES["D_eq_arm0"]["extra"].pop("mixamorig1RightArm_033", None)

    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 900, "height": 950})
        time.sleep(0.3)
        viewer = page.query_selector("#viewer")
        free_camera(page)

        mano, lado = [], []
        if REF.exists():
            mano.append(("REF foto", REF))
            lado.append(("REF foto", REF))

        for name, data in CASES.items():
            page.evaluate(
                "(pose) => window.__LSM_CONTROLLER__.applyTestPose(pose)", data
            )
            time.sleep(0.3)
            g = page.evaluate(MEASURE_JS)
            t = page.evaluate(PULGAR_JS)
            s = page.evaluate(SIMETRIA_JS)
            print(f"\n{name}")
            print(
                f"  dI={g['dI']:.2f} dM={g['dM']:.2f} dR={g['dR']:.2f} "
                f"tog={g['togIM']:.2f}/{g['togMR']:.2f} peek={g['peek']:.2f} "
                f"across={t['across4']:+.2f} frente={t['frente4']:+.2f}"
            )
            print(" ", informe(name, s))
            print(detalle(s))
            hand = page.evaluate(HAND_POS_JS)
            set_cam(page, "mano", hand)
            p_m = OUT / f"{name}_mano.png"
            viewer.screenshot(path=str(p_m))
            mano.append((name, p_m))
            set_cam(page, "lado", hand)
            p_l = OUT / f"{name}_lado.png"
            viewer.screenshot(path=str(p_l))
            lado.append((name, p_l))

        browser.close()

    hoja(mano, OUT / "_mano.png", cols=3, cell=300)
    hoja(lado, OUT / "_lado.png", cols=3, cell=300)
    (OUT / "_candidatas.json").write_text(
        json.dumps(CASES, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
