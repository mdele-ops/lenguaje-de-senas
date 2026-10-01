"""X lab 2: perfil de la lamina + que huesos jalon de toda la mano.

La foto muestra el gancho de perfil (lado del pulgar/indice al frente) y una
flecha diagonal arriba-derecha: la mano ENTERA se jala, la muneca no se dobla
sola. Se fija la forma, se busca el giro que deja ese perfil y se mide el
jacobiano de hombro/codo para el jalon.
"""
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from enfoque_r import MANO, captura, hoja
from pose_lab_e import ARM, _GET_SCENE, free_camera
from pose_lab_x import MEASURE_JS, REF, pose_x, asegurar_ref, linea
from ver_s import CAM_FOV, CAM_ORBIT, CAM_TARGET
import search_e9 as se9
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "lab_x2"
OUT.mkdir(parents=True, exist_ok=True)

se9.URL = "http://127.0.0.1:8006/practica.html?letra=%E2%97%8B&v=x2"

FOREARM = "mixamorig1RightForeArm_034"
WRIST = "mixamorig1RightHand_035"

# Gancho que se lee: indice sale del puno y se dobla en PIP/DIP, no un puno.
HOOK = dict(mcp=26, pip=68, dip=40, tcurl=0.5, taside=0.08)

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
  return {
    palm,
    x: i4.x, y: i4.y, z: i4.z,
    wx: w.x, wy: w.y, wz: w.z,
  };
}
"""
)

EJES = [
    (ARM, "x", 8),
    (ARM, "y", 8),
    (ARM, "z", 8),
    (FOREARM, "x", 8),
    (FOREARM, "y", 8),
    (FOREARM, "z", 8),
    (WRIST, "x", 12),
    (WRIST, "y", 12),
    (WRIST, "z", 12),
]


def cam(page, orbit=CAM_ORBIT):
    page.evaluate(
        """(a) => {
            const mv = document.getElementById('handViewer');
            mv.cameraTarget = a.t;
            mv.cameraOrbit = a.orbit;
            mv.fieldOfView = a.fov;
            mv.jumpCameraToGoal();
        }""",
        {"t": CAM_TARGET, "orbit": orbit, "fov": CAM_FOV},
    )
    time.sleep(0.2)


def aplicar(page, pose):
    page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
    time.sleep(0.25)


def con_extra(base, hueso, eje, grados):
    pose = json.loads(json.dumps(base))
    extra = pose.setdefault("extra", {})
    extra.setdefault(hueso, {})
    extra[hueso][eje] = extra[hueso].get(eje, 0) + grados
    if hueso == WRIST:
        mun = pose.setdefault("muneca", {})
        mun[eje] = mun.get(eje, 0) + grados
    return pose


def main():
    ref = asegurar_ref()
    orient = {
        "y55": pose_x(wy=55, **HOOK),
        "y70": pose_x(wy=70, **HOOK),
        "y80": pose_x(wy=80, **HOOK),
        "y90": pose_x(wy=90, **HOOK),
        "y70_x-15": pose_x(wy=70, wx=-15, **HOOK),
        "y80_x-12": pose_x(wy=80, wx=-12, **HOOK),
        "y70_z15": pose_x(wy=70, wz=15, **HOOK),
        "y-55": pose_x(wy=-55, **HOOK),
    }

    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 1000, "height": 1000})
        time.sleep(0.3)
        free_camera(page)
        viewer = page.query_selector("#viewer")

        items = [("REF foto", ref)] if ref else []
        for nombre, pose in orient.items():
            aplicar(page, pose)
            m = page.evaluate(MEASURE_JS)
            print(" ", linea(nombre, m))
            cam(page)
            ruta = OUT / f"{nombre}.png"
            captura(page, ruta, huesos=MANO, margen=0.42, lado=420)
            items.append((nombre, ruta))
            prod = OUT / f"{nombre}_prod.png"
            viewer.screenshot(path=str(prod))

        hoja(items, OUT / "_orient.png", cols=3, cell=360, titulo="X · perfil")

        base = pose_x(wy=80, wx=-12, **HOOK)
        aplicar(page, base)
        origen = page.evaluate(POS_JS)
        palm = origen["palm"]
        print(f"\njacobiano sobre y80_x-12  palma={palm:.4f}")
        print(f"{'hueso':34s} {'eje':4s} {'dx':>9s} {'dy':>9s} {'dz':>9s}")
        jac = {}
        for hueso, eje, paso in EJES:
            aplicar(page, con_extra(base, hueso, eje, paso))
            m = page.evaluate(POS_JS)
            dx = (m["x"] - origen["x"]) / paso / palm
            dy = (m["y"] - origen["y"]) / paso / palm
            dz = (m["z"] - origen["z"]) / paso / palm
            jac[f"{hueso}.{eje}"] = {"dx": dx, "dy": dy, "dz": dz}
            corto = hueso.replace("mixamorig1Right", "")
            print(f"{corto:34s} {eje:4s} {dx:+9.4f} {dy:+9.4f} {dz:+9.4f}")

        (OUT / "_jac.json").write_text(
            json.dumps({"palm": palm, "jac": jac}, indent=2), encoding="utf-8"
        )

        # tres jalones cortos (~0.55 palmas) para ver cual pega con la flecha
        def pull(nombre, deltas):
            pose = json.loads(json.dumps(base))
            extra = pose.setdefault("extra", {})
            mun = pose.setdefault("muneca", {})
            for hueso, eje, g in deltas:
                if hueso == WRIST:
                    mun[eje] = mun.get(eje, 0) + g
                extra.setdefault(hueso, {})
                extra[hueso][eje] = extra[hueso].get(eje, 0) + g
            aplicar(page, pose)
            m = page.evaluate(POS_JS)
            dx = (m["x"] - origen["x"]) / palm
            dy = (m["y"] - origen["y"]) / palm
            dz = (m["z"] - origen["z"]) / palm
            print(f"  pull {nombre:16s} d=({dx:+.3f},{dy:+.3f},{dz:+.3f})")
            cam(page)
            ruta = OUT / f"pull_{nombre}.png"
            captura(page, ruta, huesos=MANO, margen=0.55, lado=420)
            return (nombre, ruta)

        print("\njalones")
        pulls = [
            pull("armX+", [(ARM, "x", 12)]),
            pull("armY+", [(ARM, "y", 12)]),
            pull("foreX+", [(FOREARM, "x", 12)]),
            pull("foreX-", [(FOREARM, "x", -12)]),
            pull("armX+_foreX-", [(ARM, "x", 10), (FOREARM, "x", -10)]),
            pull("armY+_foreX-", [(ARM, "y", 10), (FOREARM, "x", -10)]),
            pull("wx-20", [(WRIST, "x", -20)]),
            pull("wx+20", [(WRIST, "x", 20)]),
        ]
        hoja(
            ([("REF foto", ref)] if ref else []) + pulls,
            OUT / "_pulls.png",
            cols=3,
            cell=360,
            titulo="X · jalon",
        )

        browser.close()
    print("listo", OUT)


if __name__ == "__main__":
    main()
