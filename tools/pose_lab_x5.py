"""X lab 5: levantar el puno (muneca.x grande) para que no se vea acostado."""
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from enfoque_r import MANO, captura, hoja
from pose_lab_e import free_camera
from pose_lab_x import MEASURE_JS, REF, pose_x, asegurar_ref
from pose_lab_x4 import FIST_JS, cam
from ver_s import CAM_FOV, CAM_ORBIT, CAM_TARGET
import search_e9 as se9
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "lab_x5"
OUT.mkdir(parents=True, exist_ok=True)
se9.URL = "http://127.0.0.1:8006/practica.html?letra=%E2%97%8B&v=x5"

HOOK = dict(mcp=32, pip=78, dip=50, tcurl=0.55, taside=0.1, t1={"y": -18})


def main():
    catalogo = json.loads((ROOT / "data" / "catalogo-lsm.json").read_text("utf-8"))
    por = {s["letra"]: s["pose"] for s in catalogo["senas"]}
    ref = asegurar_ref()
    casos = {
        "00_actual": por["X"],
        "01_A": por["A"],
        "02_L": por["L"],
        "03_I": por["I"],
        "04_y0": pose_x(arm_z=-18, **HOOK),
        "05_wx-40": pose_x(wx=-40, arm_z=-18, **HOOK),
        "06_wx-70": pose_x(wx=-70, arm_z=-18, **HOOK),
        "07_wx-90": pose_x(wx=-90, arm_z=-18, **HOOK),
        "08_wx40": pose_x(wx=40, arm_z=-18, **HOOK),
        "09_wx70": pose_x(wx=70, arm_z=-18, **HOOK),
        "10_wx-70_y-20": pose_x(wx=-70, wy=-20, arm_z=-18, **HOOK),
        "11_wx-70_y20": pose_x(wx=-70, wy=20, arm_z=-18, **HOOK),
    }
    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 1100, "height": 900})
        time.sleep(0.3)
        free_camera(page)
        viewer = page.query_selector("#viewer")
        items, prods = ([("REF", ref)] if ref else []), ([("REF", ref)] if ref else [])
        for nombre, pose in casos.items():
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
            time.sleep(0.28)
            f = page.evaluate(FIST_JS)
            m = page.evaluate(MEASURE_JS)
            print(
                f"  {nombre:16s} fistUp={f['fistUp']:+.2f} side={f['fistSide']:+.2f} "
                f"fwd={f['fistFwd']:+.2f} idxUp={m['idxUp']:+.2f} idxSide={m['idxSide']:+.2f}"
            )
            cam(page)
            r = OUT / f"{nombre}.png"
            captura(page, r, huesos=MANO, margen=0.42, lado=400)
            items.append((nombre, r))
            pr = OUT / f"{nombre}_prod.png"
            viewer.screenshot(path=str(pr))
            prods.append((nombre, pr))
        hoja(items, OUT / "_mano.png", cols=4, cell=300, titulo="X · levantar")
        hoja(prods, OUT / "_prod.png", cols=4, cell=260, titulo="X · prod levantar")
        browser.close()


if __name__ == "__main__":
    main()
