"""M lab 6: cierra de verdad los tres dedos sobre el pulgar de C_lomos.

En m5 el pulgar ya llega entre anular y menique (across ~0.78), pero los
dedos solo se empujaban con extra y curl 0: no cubren el pulgar. Aqui el
cierre lo hace `curl` (como la E), y el extra solo distingue menique y
aprieta un poco el PIP para el lomo.
"""
import json
import time
from pathlib import Path

from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright

from pose_lab_e import ARM, BONES, FINGERS, HAND_POS_JS, T1, T2, T3, free_camera, set_cam
from pose_lab_m5 import MEASURE_JS, hoja, pose_m
from pulgar_e import PULGAR_JS
from search_e9 import abrir
from simetria_e import SIMETRIA_JS, detalle, informe

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "lab_m6"
OUT.mkdir(parents=True, exist_ok=True)
REF = ROOT / "tools" / "screenshots" / "referencia" / "M_usuario.png"

import search_e9 as se9

se9.URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=m6"

T1_C = {"x": 16, "y": -60, "z": 48}


def pose_curl(ic, mc, rc, pc, spreads, tcurl, taside, t1, t2x, t3x, more=None):
    extra = {ARM: {"z": -18}, T1: dict(t1)}
    if t2x:
        extra[T2] = {"x": t2x}
    if t3x:
        extra[T3] = {"x": t3x}
    if more:
        for name, rot in more.items():
            extra[name] = {**extra.get(name, {}), **rot}
    pose = {
        "thumb": {"curl": tcurl, "aside": taside},
        "index": {"curl": ic, "spread": spreads[0]},
        "middle": {"curl": mc, "spread": spreads[1]},
        "ring": {"curl": rc, "spread": spreads[2]},
        "pinky": {"curl": pc, "spread": spreads[3]},
        "extra": extra,
    }
    return pose


CAT = json.loads((ROOT / "data" / "catalogo-lsm.json").read_text("utf-8"))
POSE_E = next(s for s in CAT["senas"] if s["letra"] == "E")["pose"]
POSE_M = next(s for s in CAT["senas"] if s["letra"] == "M")["pose"]

PIP_LOMO = {
    BONES["index"][1]: {"x": 12},
    BONES["middle"][1]: {"x": 12},
    BONES["ring"][1]: {"x": 12},
    BONES["pinky"][0]: {"x": 8},
    BONES["pinky"][1]: {"x": 16},
    BONES["pinky"][2]: {"x": 20},
}

CASES = {
    "00_actual": POSE_M,
    "01_e": POSE_E,
    "C_m5": pose_m(
        mcp=(55, 58, 60, 78),
        pip=(88, 90, 92, 105),
        dip=(32, 34, 36, 68),
        conv=4,
        tcurl=0.48, taside=0.18,
        t1=T1_C, t2x=28, t3x=18,
    ),
    "A_curl88": pose_curl(
        0.88, 0.88, 0.88, 1.0,
        (-8, -2, 4, 14),
        0.48, 0.18, T1_C, 28, 18,
        PIP_LOMO,
    ),
    "B_curl82": pose_curl(
        0.82, 0.84, 0.86, 1.0,
        (-8, -2, 4, 14),
        0.48, 0.18, T1_C, 28, 18,
        PIP_LOMO,
    ),
    "C_curl92": pose_curl(
        0.92, 0.92, 0.92, 1.0,
        (-10, -3, 5, 16),
        0.48, 0.18, T1_C, 28, 18,
        {
            **PIP_LOMO,
            BONES["index"][2]: {"x": 8},
            BONES["middle"][2]: {"x": 8},
            BONES["ring"][2]: {"x": 8},
        },
    ),
    "D_e_fingers": pose_curl(
        0.92, 0.92, 0.92, 1.0,
        (-12, -4, 4, 14),
        0.48, 0.18, T1_C, 28, 18,
        {
            BONES["index"][0]: {"x": 4.8},
            BONES["index"][1]: {"x": 6.6},
            BONES["index"][2]: {"x": 12},
            BONES["middle"][1]: {"x": 4.8},
            BONES["middle"][2]: {"x": 18},
            BONES["ring"][0]: {"x": -8.5},
            BONES["ring"][1]: {"x": 9.7},
            BONES["ring"][2]: {"x": 22},
            BONES["pinky"][0]: {"x": 6},
            BONES["pinky"][1]: {"x": 14},
            BONES["pinky"][2]: {"x": 28},
        },
    ),
    "E_thumb_fwd": pose_curl(
        0.88, 0.88, 0.88, 1.0,
        (-8, -2, 4, 14),
        0.52, 0.12,
        {"x": 20, "y": -55, "z": 44},
        26, 16,
        PIP_LOMO,
    ),
}


def main():
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
                f"peek={g['peek']:.2f} across={t['across4']:+.2f} "
                f"frente={t['frente4']:+.2f}"
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
        json.dumps({k: v for k, v in CASES.items()}, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
