"""M lab 4: tres dedos (indice, medio, anular) doblados SOBRE el pulgar.

La foto de referencia (lamina Mm) no es un puno generico ni tres dedos
colgando: palma al frente, indice/medio/anular cubren el pulgar y forman
tres lomos; el pulgar queda debajo y su yema asoma entre anular y menique;
el menique va cerrado a un lado, no forma un cuarto lomo.
"""
import json
import time
from pathlib import Path

from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright

from pose_lab_e import ARM, BONES, HAND_POS_JS, T1, T2, T3, free_camera, set_cam
from pulgar_e import PULGAR_JS
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "lab_m4"
OUT.mkdir(parents=True, exist_ok=True)
REF_SRC = ROOT / "tools" / "screenshots" / "referencia" / "M_usuario.png"

import search_e9 as se9

se9.URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=m4"


def extra_merge(*parts):
    out = {ARM: {"z": -18}}
    for part in parts:
        if not part:
            continue
        for name, rot in part.items():
            out[name] = {**out.get(name, {}), **rot}
    return out


def pose_m(
    ic=0.82,
    mc=0.82,
    rc=0.82,
    pc=0.98,
    tcurl=0.55,
    taside=-0.9,
    spreads=None,
    t1=None,
    t2=None,
    t3=None,
    more=None,
):
    spreads = spreads or (-8, -2, 4, 14)
    extra = extra_merge(
        {T1: t1} if t1 else None,
        {T2: t2} if t2 else None,
        {T3: t3} if t3 else None,
        more,
    )
    return {
        "thumb": {"curl": tcurl, "aside": taside},
        "index": {"curl": ic, "spread": spreads[0]},
        "middle": {"curl": mc, "spread": spreads[1]},
        "ring": {"curl": rc, "spread": spreads[2]},
        "pinky": {"curl": pc, "spread": spreads[3]},
        "extra": extra,
    }


CAT = json.loads((ROOT / "data" / "catalogo-lsm.json").read_text("utf-8"))
ACTUAL = next(s for s in CAT["senas"] if s["letra"] == "M")["pose"]
POSE_E = next(s for s in CAT["senas"] if s["letra"] == "E")["pose"]
POSE_T = next(s for s in CAT["senas"] if s["letra"] == "T")["pose"]
POSE_A = next(s for s in CAT["senas"] if s["letra"] == "A")["pose"]

# Pulgar de la E (barra horizontal). En la M hay que llevarlo mas lejos,
# hasta que la yema asome entre anular y menique.
T1_E = {"x": 60, "y": -35, "z": 78}
T2_E = {"x": 24}
T3_E = {"x": -11}

CASES = {
    "00_actual": ACTUAL,
    "01_e": POSE_E,
    "02_t": POSE_T,
    "03_a": POSE_A,
    # Partir de la E: menique mas cerrado, pulgar mas largo (menos curl).
    "04_e_pinky": pose_m(
        ic=0.92, mc=0.92, rc=0.92, pc=1.0,
        tcurl=0.45, taside=-0.96,
        t1=T1_E, t2=T2_E, t3=T3_E,
        more={
            BONES["pinky"][0]: {"x": 8},
            BONES["pinky"][1]: {"x": 12},
            BONES["pinky"][2]: {"x": 18},
        },
    ),
    # Tres lomos: curl un poco menor que la E para no enrollar las yemas.
    "05_drape": pose_m(
        ic=0.78, mc=0.80, rc=0.82, pc=0.98,
        tcurl=0.42, taside=-0.96,
        t1=T1_E, t2={"x": 40}, t3={"x": 10},
    ),
    # Pulgar mas atravesado (mas z en la base).
    "06_across": pose_m(
        ic=0.80, mc=0.82, rc=0.84, pc=0.98,
        tcurl=0.38, taside=-1.0,
        t1={"x": 45, "y": -20, "z": 95},
        t2={"x": 30}, t3={"x": 8},
    ),
    # Pulgar mas metido bajo los tres, yema hacia el menique.
    "07_under": pose_m(
        ic=0.84, mc=0.85, rc=0.86, pc=0.99,
        tcurl=0.50, taside=-0.85,
        t1={"x": 70, "y": -45, "z": 70},
        t2={"x": 18}, t3={"x": -8},
        more={
            BONES["index"][0]: {"x": 6},
            BONES["middle"][0]: {"x": 4},
            BONES["ring"][0]: {"x": 2},
            BONES["pinky"][0]: {"x": 10},
            BONES["pinky"][2]: {"x": 22},
        },
    ),
    # Puno tipo A con el pulgar metido (twist/aside de la T, mas recorrido).
    "08_fist_in": pose_m(
        ic=0.88, mc=0.88, rc=0.88, pc=0.98,
        tcurl=0.55, taside=0.15,
        spreads=(-4, 0, 4, 10),
        t1={"x": 20, "y": -55, "z": 40},
        t2={"x": 25}, t3={"x": 15},
    ),
    # Misma familia que 07, tres dedos mas juntos.
    "09_tight": pose_m(
        ic=0.83, mc=0.84, rc=0.85, pc=0.99,
        tcurl=0.48, taside=-0.92,
        spreads=(-10, -2, 6, 16),
        t1={"x": 55, "y": -30, "z": 85},
        t2={"x": 28}, t3={"x": 0},
        more={
            BONES["pinky"][1]: {"x": 14},
            BONES["pinky"][2]: {"x": 24},
        },
    ),
    # Pulgar casi extendido cruzando hasta el menique.
    "10_long": pose_m(
        ic=0.80, mc=0.82, rc=0.84, pc=0.98,
        tcurl=0.28, taside=-1.0,
        t1={"x": 50, "y": -15, "z": 100},
        t2={"x": 12}, t3={"x": 4},
    ),
}


def hoja(items, out_path, cols=4, cell=280):
    lh = 22
    filas = (len(items) + cols - 1) // cols
    canvas = Image.new("RGB", (cols * cell, filas * (cell + lh)), (245, 245, 248))
    draw = ImageDraw.Draw(canvas)
    for i, (name, path) in enumerate(items):
        x, y = (i % cols) * cell, (i // cols) * (cell + lh)
        canvas.paste(
            Image.open(path).convert("RGB").resize((cell, cell), Image.LANCZOS),
            (x, y),
        )
        draw.rectangle([x, y + cell, x + cell, y + cell + lh], fill=(20, 30, 50))
        draw.text((x + 6, y + cell + 6), name, fill=(255, 255, 255))
    canvas.save(out_path)
    print("Hoja:", out_path)


def main():
    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 900, "height": 950})
        time.sleep(0.4)
        viewer = page.query_selector("#viewer")
        free_camera(page)

        mano, lado = [], []
        if REF_SRC.exists():
            mano.append(("REF foto", REF_SRC))
            lado.append(("REF foto", REF_SRC))

        for name, data in CASES.items():
            page.evaluate(
                "(pose) => window.__LSM_CONTROLLER__.applyTestPose(pose)", data
            )
            time.sleep(0.28)
            m = page.evaluate(PULGAR_JS)
            print(
                f"{name:14s} across4={m['across4']:+.2f} frente4={m['frente4']:+.2f} "
                f"alto4={m['alto4']:.2f} frenteMax={m['frenteMax']:+.2f}"
            )
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

    hoja(mano, OUT / "_mano.png", cols=4, cell=280)
    hoja(lado, OUT / "_lado.png", cols=4, cell=280)


if __name__ == "__main__":
    main()
