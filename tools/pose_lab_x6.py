"""X lab 6: de pie (wx ~70) y palma hacia el cuerpo, como la foto."""
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from enfoque_r import MANO, captura, hoja
from pose_lab_e import ARM, free_camera
from pose_lab_x import MEASURE_JS, REF, pose_x, asegurar_ref
from pose_lab_x2 import FOREARM
from pose_lab_x4 import FIST_JS, POS_JS, cam
from ver_s import CAM_FOV, CAM_ORBIT, CAM_TARGET
import search_e9 as se9
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "lab_x6"
OUT.mkdir(parents=True, exist_ok=True)
se9.URL = "http://127.0.0.1:8006/practica.html?letra=%E2%97%8B&v=x6"
HOOK = dict(mcp=32, pip=78, dip=50, tcurl=0.55, taside=0.1, t1={"y": -18})


def main():
    catalogo = json.loads((ROOT / "data" / "catalogo-lsm.json").read_text("utf-8"))
    actual = next(s for s in catalogo["senas"] if s["letra"] == "X")["pose"]
    ref = asegurar_ref()
    casos = {
        "00_actual": actual,
        "01_wx70": pose_x(wx=70, arm_z=-18, **HOOK),
        "02_wx70_y20": pose_x(wx=70, wy=20, arm_z=-18, **HOOK),
        "03_wx70_y-25": pose_x(wx=70, wy=-25, arm_z=-18, **HOOK),
        "04_wx55_y-20": pose_x(wx=55, wy=-20, arm_z=-18, **HOOK),
        "05_wx55": pose_x(wx=55, arm_z=-18, **HOOK),
        "06_wx80": pose_x(wx=80, arm_z=-18, **HOOK),
        "07_wx70_z-15": pose_x(wx=70, wz=-15, arm_z=-18, **HOOK),
        "08_wx70_z15": pose_x(wx=70, wz=15, arm_z=-18, **HOOK),
        "09_wx60_y-15": pose_x(wx=60, wy=-15, arm_z=-18, **HOOK),
    }
    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 1100, "height": 900})
        time.sleep(0.3)
        free_camera(page)
        viewer = page.query_selector("#viewer")
        items = [("REF", ref)] if ref else []
        prods = [("REF", ref)] if ref else []
        for nombre, pose in casos.items():
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
            time.sleep(0.28)
            f = page.evaluate(FIST_JS)
            m = page.evaluate(MEASURE_JS)
            print(
                f"  {nombre:16s} fistUp={f['fistUp']:+.2f} fwd={f['fistFwd']:+.2f} "
                f"idxUp={m['idxUp']:+.2f} idxSide={m['idxSide']:+.2f} palmNz={m['palmNz']:+.2f}"
            )
            cam(page)
            r = OUT / f"{nombre}.png"
            captura(page, r, huesos=MANO, margen=0.45, lado=400)
            items.append((nombre, r))
            pr = OUT / f"{nombre}_prod.png"
            viewer.screenshot(path=str(pr))
            prods.append((nombre, pr))
        hoja(items, OUT / "_mano.png", cols=4, cell=300, titulo="X · de pie + palma")
        hoja(prods, OUT / "_prod.png", cols=4, cell=260, titulo="X · prod de pie")

        # jacobiano de la candidata que mas se acerca a la foto
        base = pose_x(wx=70, arm_z=-18, **HOOK)
        page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", base)
        time.sleep(0.25)
        origen = page.evaluate(POS_JS)
        palm = origen["palm"]
        print("\njacobiano wx70")
        for hueso, eje, paso in [
            (ARM, "x", 8), (ARM, "z", 8),
            (FOREARM, "x", 8), (FOREARM, "z", 8),
        ]:
            pose = json.loads(json.dumps(base))
            extra = pose.setdefault("extra", {})
            extra.setdefault(hueso, {})
            extra[hueso][eje] = extra[hueso].get(eje, 0) + paso
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
            time.sleep(0.2)
            q = page.evaluate(POS_JS)
            dx = (q["x"] - origen["x"]) / paso / palm
            dy = (q["y"] - origen["y"]) / paso / palm
            dz = (q["z"] - origen["z"]) / paso / palm
            print(f"  {hueso[-7:]:10s} {eje}  dx={dx:+.4f} dy={dy:+.4f} dz={dz:+.4f}")
        browser.close()


if __name__ == "__main__":
    main()
