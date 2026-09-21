"""X lab 4: la mano tiene que ir DE PIE, no acostada.

muneca.y 72 tumbo el puno de lado. En la foto los nudillos van verticales
y el antebrazo entra en diagonal desde abajo; es la misma postura de la A/I,
con el indice en gancho. Aqui se compara contra A/I y se quita ese giro.
"""
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from enfoque_r import MANO, captura, hoja
from pose_lab_e import ARM, T1, _GET_SCENE, free_camera
from pose_lab_x import MEASURE_JS, REF, pose_x, asegurar_ref
from ver_s import CAM_FOV, CAM_ORBIT, CAM_TARGET
import search_e9 as se9
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "lab_x4"
OUT.mkdir(parents=True, exist_ok=True)

se9.URL = "http://127.0.0.1:8006/practica.html?letra=%E2%97%8B&v=x4"

FOREARM = "mixamorig1RightForeArm_034"
HOOK = dict(mcp=32, pip=78, dip=50, tcurl=0.55, taside=0.1, t1={"y": -18})

FIST_JS = (
    """
() => {
  const mv = document.getElementById('handViewer');
"""
    + _GET_SCENE
    + """
  const scene = getScene(mv);
  scene.updateMatrixWorld(true);
  const B = {};
  scene.traverse((o) => { if (o && o.name) B[o.name] = o; });
  const P = (n) => {
    const e = B[n].matrixWorld.elements;
    return { x: e[12], y: e[13], z: e[14] };
  };
  const sub = (a, b) => ({ x: a.x-b.x, y: a.y-b.y, z: a.z-b.z });
  const nrm = (v) => {
    const l = Math.hypot(v.x, v.y, v.z) || 1;
    return { x: v.x/l, y: v.y/l, z: v.z/l };
  };
  const w = P('mixamorig1RightHand_035');
  const i1 = P('mixamorig1RightHandIndex1_040');
  const m1 = P('mixamorig1RightHandMiddle1_044');
  const p1 = P('mixamorig1RightHandPinky1_052');
  const palm = Math.hypot(w.x-i1.x, w.y-i1.y, w.z-i1.z) || 1;
  const eje = nrm(sub(m1, w));
  return {
    fistUp: eje.y,
    fistSide: eje.x,
    fistFwd: eje.z,
    thumbTop: (P('mixamorig1RightHandThumb4_039').y - i1.y) / palm,
  };
}
"""
)

POS_JS = (
    """
() => {
  const mv = document.getElementById('handViewer');
"""
    + _GET_SCENE
    + """
  const scene = getScene(mv);
  scene.updateMatrixWorld(true);
  const B = {};
  scene.traverse((o) => { if (o && o.name) B[o.name] = o; });
  const P = (n) => {
    const e = B[n].matrixWorld.elements;
    return { x: e[12], y: e[13], z: e[14] };
  };
  const w = P('mixamorig1RightHand_035');
  const i1 = P('mixamorig1RightHandIndex1_040');
  const i4 = P('mixamorig1RightHandIndex4_043');
  const palm = Math.hypot(w.x-i1.x, w.y-i1.y, w.z-i1.z) || 1;
  return { palm, x: i4.x, y: i4.y, z: i4.z };
}
"""
)


def cam(page):
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
    time.sleep(0.2)


def aplicar(page, pose):
    page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
    time.sleep(0.28)


def pose_pie(wy=0, wx=0, wz=0):
    return pose_x(wy=wy, wx=wx, wz=wz, arm_z=-18, **HOOK)


def main():
    catalogo = json.loads((ROOT / "data" / "catalogo-lsm.json").read_text("utf-8"))
    por = {s["letra"]: s["pose"] for s in catalogo["senas"]}
    ref = asegurar_ref()

    casos = {
        "00_actual": por["X"],
        "01_A": por["A"],
        "02_I": por["I"],
        "03_y0": pose_pie(),
        "04_y-12": pose_pie(wy=-12),
        "05_wx-15": pose_pie(wx=-15),
        "06_wz20": pose_pie(wz=20),
        "07_wz-20": pose_pie(wz=-20),
        "08_y20": pose_pie(wy=20),
        "09_y-20": pose_pie(wy=-20),
        "10_wx10": pose_pie(wx=10),
        "11_y0_wx8": pose_pie(wx=8),
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
            aplicar(page, pose)
            f = page.evaluate(FIST_JS)
            m = page.evaluate(MEASURE_JS)
            print(
                f"  {nombre:12s} fistUp={f['fistUp']:+.2f} side={f['fistSide']:+.2f} "
                f"fwd={f['fistFwd']:+.2f} hook={m['hookPIP']:.0f} idxUp={m['idxUp']:+.2f}"
            )
            cam(page)
            ruta = OUT / f"{nombre}.png"
            captura(page, ruta, huesos=MANO, margen=0.42, lado=420)
            items.append((nombre, ruta))
            prod = OUT / f"{nombre}_prod.png"
            viewer.screenshot(path=str(prod))
            prods.append((nombre, prod))

        hoja(items, OUT / "_mano.png", cols=4, cell=320, titulo="X · de pie")
        hoja(prods, OUT / "_prod.png", cols=4, cell=280, titulo="X · produccion")

        # jacobiano sobre la pose de pie (y0)
        base = pose_pie()
        aplicar(page, base)
        origen = page.evaluate(POS_JS)
        palm = origen["palm"]
        ejes = [
            (ARM, "x", 8),
            (ARM, "y", 8),
            (ARM, "z", 8),
            (FOREARM, "x", 8),
            (FOREARM, "y", 8),
            (FOREARM, "z", 8),
        ]
        print(f"\njacobiano y0  palma={palm:.4f}")
        jac = {}
        for hueso, eje, paso in ejes:
            pose = json.loads(json.dumps(base))
            extra = pose.setdefault("extra", {})
            extra.setdefault(hueso, {})
            extra[hueso][eje] = extra[hueso].get(eje, 0) + paso
            aplicar(page, pose)
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
