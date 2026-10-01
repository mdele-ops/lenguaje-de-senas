"""N lab 4: afinado sobre A_corto (across 0.60). Muneca ligera, no colgante."""
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from pose_lab_e import HAND_POS_JS, free_camera, set_cam
from pose_lab_m5 import hoja
from pose_lab_n3 import pose_n, T_CORTO
from pulgar_e import PULGAR_JS
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "lab_n4"
OUT.mkdir(parents=True, exist_ok=True)
REF = ROOT / "tools" / "screenshots" / "referencia" / "N_usuario.png"

import search_e9 as se9

se9.URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=n4"

CAT = json.loads((ROOT / "data" / "catalogo-lsm.json").read_text("utf-8"))
CASES = {
    "00_actual": next(s for s in CAT["senas"] if s["letra"] == "N")["pose"],
    "A_recto": pose_n(**T_CORTO),
    "B_x28": pose_n(**T_CORTO, mx=28),
    "C_x40": pose_n(**T_CORTO, mx=40),
    "D_x28_arm": pose_n(**T_CORTO, mx=28, arm_z=-18),
    "E_x35_arm": pose_n(**T_CORTO, mx=35, arm_z=-18),
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
            prod.append(("REF foto", REF))

        poses = {}
        for name, data in CASES.items():
            poses[name] = data
            page.evaluate(
                "(pose) => window.__LSM_CONTROLLER__.applyTestPose(pose)", data
            )
            time.sleep(0.32)
            t = page.evaluate(PULGAR_JS)
            print(
                f"{name:14s} across={t['across4']:+.2f} frente={t['frente4']:+.2f} "
                f"alto={t['alto4']:+.2f}"
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

    hoja(frente, OUT / "_frente.png", cols=4, cell=300)
    hoja(lado, OUT / "_lado.png", cols=4, cell=300)
    hoja(prod, OUT / "_prod.png", cols=4, cell=300)
    (OUT / "_poses.json").write_text(
        json.dumps(poses, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
