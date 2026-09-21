"""X lab 9: candidata z-90 + wx20 (puno de pie, gancho a la izquierda)."""
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from enfoque_r import MANO, captura, hoja
from pose_lab_e import ARM, T1, T2, free_camera
from pose_lab_x import MEASURE_JS, pose_x
from pose_lab_x2 import FOREARM, POS_JS
from pose_lab_x4 import FIST_JS, cam
import search_e9 as se9
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "lab_x9"
OUT.mkdir(parents=True, exist_ok=True)
REF = ROOT / "tools" / "screenshots" / "referencia" / "X_usuario.png"

se9.URL = "http://127.0.0.1:8006/practica.html?letra=%E2%97%8B&v=x9"


def pose_fin(mcp=18, pip=78, dip=58, tcurl=0.45, taside=0.08,
             wx=20, wy=0, wz=-90, t1=None, t2x=0, fist=1.0):
    extra = {
        ARM: {"z": -18},
        "mixamorig1RightHandIndex1_040": {"x": mcp},
        "mixamorig1RightHandIndex2_041": {"x": pip},
        "mixamorig1RightHandIndex3_042": {"x": dip},
    }
    if t1:
        extra[T1] = t1
    if t2x:
        extra[T2] = {"x": t2x}
    muneca = {"z": wz}
    if wx:
        muneca["x"] = wx
    if wy:
        muneca["y"] = wy
    return {
        "thumb": {"curl": tcurl, "aside": taside},
        "index": {"curl": 0.0},
        "middle": {"curl": fist},
        "ring": {"curl": fist},
        "pinky": {"curl": fist},
        "muneca": muneca,
        "extra": extra,
    }


def main():
    catalogo = json.loads((ROOT / "data" / "catalogo-lsm.json").read_text("utf-8"))
    actual = next(s for s in catalogo["senas"] if s["letra"] == "X")["pose"]

    casos = {
        "00_actual": actual,
        "01_base": pose_fin(),
        "02_wx25": pose_fin(wx=25),
        "03_wx15": pose_fin(wx=15),
        "04_hook_duro": pose_fin(mcp=14, pip=84, dip=64),
        "05_hook_largo": pose_fin(mcp=24, pip=70, dip=52),
        "06_z-80": pose_fin(wz=-80),
        "07_thumb": pose_fin(tcurl=0.4, taside=0.05, t1={"y": -10, "z": 10}, t2x=12),
        "08_y-12": pose_fin(wy=-12),
        "09_y12": pose_fin(wy=12),
    }

    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 1100, "height": 900})
        time.sleep(2.2)
        free_camera(page)
        viewer = page.query_selector("#viewer")

        items = [("REF foto", REF)] if REF.exists() else []
        prods = [("REF foto", REF)] if REF.exists() else []
        for nombre, pose in casos.items():
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
            time.sleep(0.35)
            f = page.evaluate(FIST_JS)
            m = page.evaluate(MEASURE_JS)
            print(
                f"  {nombre:14s} fistUp={f['fistUp']:+.2f} side={f['fistSide']:+.2f} "
                f"fwd={f['fistFwd']:+.2f} idx=({m['idxSide']:+.2f},{m['idxUp']:+.2f},"
                f"{m['idxFwd']:+.2f}) hook={m['hookPIP']:.0f}/{m['hookDIP']:.0f} "
                f"len={m['idxLen']:.2f} puno={m['puno']:.2f} thH={m['thH']:+.2f}"
            )
            cam(page)
            r = OUT / f"{nombre}.png"
            captura(page, r, huesos=MANO, margen=0.5, lado=500)
            items.append((nombre, r))
            pr = OUT / f"{nombre}_prod.png"
            viewer.screenshot(path=str(pr))
            prods.append((nombre, pr))

        hoja(items, OUT / "_mano.png", cols=4, cell=360, titulo="X · gancho de pie")
        hoja(prods, OUT / "_prod.png", cols=4, cell=280, titulo="X · prod gancho de pie")

        base = pose_fin()
        page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", base)
        time.sleep(0.3)
        origen = page.evaluate(POS_JS)
        palm = origen["palm"]
        print("\njalon ForeArm x10 z-10 sobre 01_base")
        pose = json.loads(json.dumps(base))
        pose["extra"][FOREARM] = {"x": 10, "z": -10}
        page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
        time.sleep(0.25)
        q = page.evaluate(POS_JS)
        dx = (q["x"] - origen["x"]) / palm
        dy = (q["y"] - origen["y"]) / palm
        print(f"  dx={dx:+.3f} dy={dy:+.3f}")
        cam(page)
        captura(page, OUT / "jalon.png", huesos=MANO, margen=0.55, lado=500)
        browser.close()
    print("listo", OUT)


if __name__ == "__main__":
    main()
