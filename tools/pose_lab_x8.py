"""X lab 8: puno DE PIE y gancho de perfil, como la foto.

wx 70 (actual) apunta el puno a la camara (fistFwd 0.99).
wy 72 lo acuesta (fistSide -0.93) y el usuario lo rechazo.
z -90 es el unico de x7 con fistUp ~ 1. Aqui se barre z negativo y
giros chicos de y/x para que el gancho se lea a la izquierda.
"""
import json
import shutil
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from enfoque_r import MANO, captura, hoja
from pose_lab_e import ARM, T1, free_camera
from pose_lab_x import MEASURE_JS, pose_x, linea
from pose_lab_x2 import FOREARM, POS_JS
from pose_lab_x4 import FIST_JS, cam
import search_e9 as se9
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "lab_x8"
OUT.mkdir(parents=True, exist_ok=True)
REF = ROOT / "tools" / "screenshots" / "referencia" / "X_usuario.png"

se9.URL = "http://127.0.0.1:8006/practica.html?letra=%E2%97%8B&v=x8"

HOOK = dict(mcp=32, pip=78, dip=50, tcurl=0.55, taside=0.1, t1={"y": -18})


def main():
    catalogo = json.loads((ROOT / "data" / "catalogo-lsm.json").read_text("utf-8"))
    por = {s["letra"]: s["pose"] for s in catalogo["senas"]}

    casos = {
        "00_actual": por["X"],
        "01_A": por["A"],
        "02_y0": pose_x(arm_z=-18, **HOOK),
        "03_z-45": pose_x(wz=-45, arm_z=-18, **HOOK),
        "04_z-70": pose_x(wz=-70, arm_z=-18, **HOOK),
        "05_z-90": pose_x(wz=-90, arm_z=-18, **HOOK),
        "06_z-110": pose_x(wz=-110, arm_z=-18, **HOOK),
        "07_z-90_y20": pose_x(wz=-90, wy=20, arm_z=-18, **HOOK),
        "08_z-90_y-20": pose_x(wz=-90, wy=-20, arm_z=-18, **HOOK),
        "09_z-90_y40": pose_x(wz=-90, wy=40, arm_z=-18, **HOOK),
        "10_z-90_wx15": pose_x(wz=-90, wx=15, arm_z=-18, **HOOK),
        "11_z-90_wx-15": pose_x(wz=-90, wx=-15, arm_z=-18, **HOOK),
        "12_z-80_y-15": pose_x(wz=-80, wy=-15, arm_z=-18, **HOOK),
        "13_z-90_hook": pose_x(
            wz=-90, mcp=20, pip=72, dip=62, tcurl=0.45, taside=0.05,
            t1={"y": -8, "z": 8}, arm_z=-18,
        ),
    }

    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 1100, "height": 900})
        time.sleep(0.3)
        free_camera(page)
        viewer = page.query_selector("#viewer")

        items = [("REF foto", REF)] if REF.exists() else []
        prods = [("REF foto", REF)] if REF.exists() else []
        for nombre, pose in casos.items():
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
            time.sleep(0.28)
            f = page.evaluate(FIST_JS)
            m = page.evaluate(MEASURE_JS)
            print(
                f"  {nombre:16s} fistUp={f['fistUp']:+.2f} side={f['fistSide']:+.2f} "
                f"fwd={f['fistFwd']:+.2f} idxS={m['idxSide']:+.2f} idxU={m['idxUp']:+.2f} "
                f"idxF={m['idxFwd']:+.2f} hook={m['hookPIP']:.0f}/{m['hookDIP']:.0f} "
                f"thH={m['thH']:+.2f}"
            )
            cam(page)
            r = OUT / f"{nombre}.png"
            captura(page, r, huesos=MANO, margen=0.48, lado=480)
            items.append((nombre, r))
            pr = OUT / f"{nombre}_prod.png"
            viewer.screenshot(path=str(pr))
            prods.append((nombre, pr))

        hoja(items, OUT / "_mano.png", cols=4, cell=340, titulo="X · puno de pie")
        hoja(prods, OUT / "_prod.png", cols=4, cell=280, titulo="X · prod de pie")

        # jacobiano de la mas vertical (z-90)
        base = pose_x(wz=-90, arm_z=-18, **HOOK)
        page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", base)
        time.sleep(0.25)
        origen = page.evaluate(POS_JS)
        palm = origen["palm"]
        print(f"\njacobiano z-90  palma={palm:.4f}")
        jac = {}
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
            jac[f"{hueso}.{eje}"] = {"dx": dx, "dy": dy, "dz": dz}
            corto = hueso.replace("mixamorig1Right", "")
            print(f"  {corto:22s} {eje}  dx={dx:+.4f} dy={dy:+.4f} dz={dz:+.4f}")
        (OUT / "_jac.json").write_text(json.dumps(jac, indent=2), encoding="utf-8")
        browser.close()
    print("listo", OUT)


if __name__ == "__main__":
    main()
