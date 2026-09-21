"""X lab 7: perfil de la lamina, gancho a la izquierda (como G/H).

La X actual (muneca.x 70) deja el gancho hacia ARRIBA, como la A/I. En la
foto el indice enganchado apunta a la IZQUIERDA, visto de 3/4 por el dorso:
es la misma orientacion de la G y la H (muneca.z ~ 90), no un puno de pie.
El y:72 anterior recostaba la palma de lado y el usuario lo rechazo.
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
from ver_s import CAM_FOV, CAM_ORBIT, CAM_TARGET
import search_e9 as se9
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "lab_x7"
OUT.mkdir(parents=True, exist_ok=True)

REF_SRC = Path(
    r"C:\Users\KZTRDG\.cursor\projects"
    r"\c-Users-KZTRDG-General-Motors-Christian-Osvaldo-Partida-Cadena-Becarios-Manu-Lenguaje-de-se-as"
    r"\assets"
    r"\c__Users_KZTRDG_AppData_Roaming_Cursor_User_workspaceStorage"
    r"_e58e5485bac69e9b6ccd69cb178bd5da_images"
    r"\image-4bfef889-eaca-4d8e-a649-22d4cf92793e.png"
)
REF = ROOT / "tools" / "screenshots" / "referencia" / "X_usuario.png"

se9.URL = "http://127.0.0.1:8006/practica.html?letra=%E2%97%8B&v=x7"

HOOK = dict(mcp=32, pip=78, dip=50, tcurl=0.55, taside=0.1, t1={"y": -18})


def asegurar_ref():
    REF.parent.mkdir(parents=True, exist_ok=True)
    if REF_SRC.exists():
        shutil.copy2(REF_SRC, REF)
    return REF if REF.exists() else None


def main():
    catalogo = json.loads((ROOT / "data" / "catalogo-lsm.json").read_text("utf-8"))
    por = {s["letra"]: s["pose"] for s in catalogo["senas"]}
    ref = asegurar_ref()

    casos = {
        "00_actual": por["X"],
        "01_G": por["G"],
        "02_z90": pose_x(wz=90, arm_z=-18, **HOOK),
        "03_z-90": pose_x(wz=-90, arm_z=-18, **HOOK),
        "04_z90_y25": pose_x(wz=90, wy=25, arm_z=-18, **HOOK),
        "05_z90_y-25": pose_x(wz=90, wy=-25, arm_z=-18, **HOOK),
        "06_z90_y40": pose_x(wz=90, wy=40, arm_z=-18, **HOOK),
        "07_z80": pose_x(wz=80, arm_z=-18, **HOOK),
        "08_z100": pose_x(wz=100, arm_z=-18, **HOOK),
        "09_z90_wx-12": pose_x(wz=90, wx=-12, arm_z=-18, **HOOK),
        "10_z90_wx12": pose_x(wz=90, wx=12, arm_z=-18, **HOOK),
        "11_y72_wx-10": pose_x(wy=72, wx=-10, arm_z=-18, **HOOK),
        "12_z90_y20_wx-10": pose_x(wz=90, wy=20, wx=-10, arm_z=-18, **HOOK),
        "13_hook_z90": pose_x(wz=90, mcp=24, pip=70, dip=58, tcurl=0.5,
                              taside=0.08, t1={"y": -12}, arm_z=-18),
    }

    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 1100, "height": 900})
        time.sleep(0.3)
        free_camera(page)
        viewer = page.query_selector("#viewer")

        items = [("REF foto", ref)] if ref else []
        prods = [("REF foto", ref)] if ref else []
        for nombre, pose in casos.items():
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
            time.sleep(0.28)
            f = page.evaluate(FIST_JS)
            m = page.evaluate(MEASURE_JS)
            print(
                f"  {nombre:18s} fistUp={f['fistUp']:+.2f} side={f['fistSide']:+.2f} "
                f"fwd={f['fistFwd']:+.2f}  {linea(nombre, m)}"
            )
            cam(page)
            r = OUT / f"{nombre}.png"
            captura(page, r, huesos=MANO, margen=0.45, lado=400)
            items.append((nombre, r))
            pr = OUT / f"{nombre}_prod.png"
            viewer.screenshot(path=str(pr))
            prods.append((nombre, pr))

        hoja(items, OUT / "_mano.png", cols=4, cell=300, titulo="X · gancho a la izquierda")
        hoja(prods, OUT / "_prod.png", cols=4, cell=260, titulo="X · produccion")

        # jacobiano sobre z90 (la orientacion de G/H)
        base = pose_x(wz=90, arm_z=-18, **HOOK)
        page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", base)
        time.sleep(0.25)
        origen = page.evaluate(POS_JS)
        palm = origen["palm"]
        print(f"\njacobiano z90  palma={palm:.4f}")
        jac = {}
        for hueso, eje, paso in [
            (ARM, "x", 8), (ARM, "y", 8), (ARM, "z", 8),
            (FOREARM, "x", 8), (FOREARM, "y", 8), (FOREARM, "z", 8),
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
