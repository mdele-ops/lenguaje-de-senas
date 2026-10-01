"""X lab 1: gancho del indice, puño cerrado y perfil de la lamina.

La X del catalogo es un puño casi cerrado (index.curl 0.85) y no se mueve.
En la foto el indice sale del puño doblado en PIP/DIP (gancho, no puño),
el pulgar se recuesta al costado del medio, palma hacia el cuerpo, y hay
un jalon diagonal de toda la mano. Este lab solo busca la FORMA y la
orientacion; el movimiento va en un segundo paso.
"""
import json
import shutil
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from enfoque_r import MANO, captura, hoja
from pose_lab_e import T1, T2, _GET_SCENE, free_camera
from ver_s import CAM_FOV, CAM_ORBIT, CAM_TARGET
import search_e9 as se9
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "lab_x"
OUT.mkdir(parents=True, exist_ok=True)
REF_SRC = Path(
    r"C:\Users\KZTRDG\.cursor\projects"
    r"\c-Users-KZTRDG-General-Motors-Christian-Osvaldo-Partida-Cadena-Becarios-Manu-Lenguaje-de-se-as"
    r"\assets"
    r"\c__Users_KZTRDG_AppData_Roaming_Cursor_User_workspaceStorage"
    r"_e58e5485bac69e9b6ccd69cb178bd5da_images"
    r"\image-1d0d3d58-35d4-432c-a553-d6490dc68dfd.png"
)
REF = ROOT / "tools" / "screenshots" / "referencia" / "X_usuario.png"

se9.URL = "http://127.0.0.1:8006/practica.html?letra=%E2%97%8B&v=x1"

I1 = "mixamorig1RightHandIndex1_040"
I2 = "mixamorig1RightHandIndex2_041"
I3 = "mixamorig1RightHandIndex3_042"
ARM = "mixamorig1RightArm_033"

MEASURE_JS = (
    """
() => {
  const mv = document.getElementById('handViewer');
"""
    + _GET_SCENE
    + """
  const scene = getScene(mv);
  if (!scene) return { error: 'no-scene' };
  scene.updateMatrixWorld(true);
  const B = {};
  scene.traverse((o) => { if (o && o.name) B[o.name] = o; });
  const P = (n) => {
    const b = B[n];
    if (!b || !b.matrixWorld) return null;
    const e = b.matrixWorld.elements;
    return { x: e[12], y: e[13], z: e[14] };
  };
  const sub = (a, b) => ({ x: a.x-b.x, y: a.y-b.y, z: a.z-b.z });
  const dot = (a, b) => a.x*b.x + a.y*b.y + a.z*b.z;
  const cross = (a, b) => ({
    x: a.y*b.z - a.z*b.y, y: a.z*b.x - a.x*b.z, z: a.x*b.y - a.y*b.x
  });
  const norm = (v) => {
    const l = Math.hypot(v.x, v.y, v.z) || 1;
    return { x: v.x/l, y: v.y/l, z: v.z/l };
  };
  const d = (a, b) => Math.hypot(a.x-b.x, a.y-b.y, a.z-b.z);
  const ang = (u, w) => {
    const c = Math.max(-1, Math.min(1, dot(u, w)));
    return Math.acos(c) * 180 / Math.PI;
  };

  const wrist = P('mixamorig1RightHand_035');
  const i1 = P('mixamorig1RightHandIndex1_040');
  const i2 = P('mixamorig1RightHandIndex2_041');
  const i3 = P('mixamorig1RightHandIndex3_042');
  const i4 = P('mixamorig1RightHandIndex4_043');
  const m1 = P('mixamorig1RightHandMiddle1_044');
  const m4 = P('mixamorig1RightHandMiddle4_047');
  const r4 = P('mixamorig1RightHandRing4_051');
  const p4 = P('mixamorig1RightHandPinky4_055');
  const t4 = P('mixamorig1RightHandThumb4_039');
  const palm = d(wrist, i1) || 1;

  const vI = norm(sub(i4, i1));
  const vProx = norm(sub(i2, i1));
  const vMid = norm(sub(i3, i2));
  const vDist = norm(sub(i4, i3));
  const palmN = norm(cross(sub(i1, wrist), sub(m1, wrist)));

  return {
    palm,
    hookPIP: ang(vProx, vMid),
    hookDIP: ang(vMid, vDist),
    idxLen: d(i1, i4) / palm,
    idxUp: vI.y,
    idxFwd: vI.z,
    idxSide: vI.x,
    midFold: d(m1, m4) / palm,
    puno: Math.max(d(m1, m4), d(P('mixamorig1RightHandRing1_048'), r4),
                   d(P('mixamorig1RightHandPinky1_052'), p4)) / palm,
    thLat: (t4.x - wrist.x) / palm,
    thH: (t4.y - i1.y) / palm,
    palmNx: palmN.x,
    palmNy: palmN.y,
    palmNz: palmN.z,
  };
}
"""
)


def pose_x(icurl=0.0, mcp=28, pip=70, dip=42, tcurl=0.5, taside=0.05,
           wy=0, wx=0, wz=0, arm_z=-18, t1=None):
    extra = {
        ARM: {"z": arm_z},
        I1: {"x": mcp},
        I2: {"x": pip},
        I3: {"x": dip},
    }
    if t1:
        extra[T1] = t1
    muneca = {}
    if wx:
        muneca["x"] = wx
    if wy:
        muneca["y"] = wy
    if wz:
        muneca["z"] = wz
    pose = {
        "thumb": {"curl": tcurl, "aside": taside},
        "index": {"curl": icurl},
        "middle": {"curl": 0.95},
        "ring": {"curl": 0.95},
        "pinky": {"curl": 0.95},
        "extra": extra,
    }
    if muneca:
        pose["muneca"] = muneca
    return pose


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
    time.sleep(0.22)


def linea(nombre, m):
    return (
        f"{nombre:22s} hook={m['hookPIP']:5.1f}/{m['hookDIP']:5.1f} "
        f"idxLen={m['idxLen']:.2f} dir=({m['idxSide']:+.2f},{m['idxUp']:+.2f},{m['idxFwd']:+.2f}) "
        f"puno={m['puno']:.2f} palmN=({m['palmNx']:+.2f},{m['palmNz']:+.2f}) "
        f"thH={m['thH']:+.2f}"
    )


def asegurar_ref():
    REF.parent.mkdir(parents=True, exist_ok=True)
    if REF_SRC.exists():
        shutil.copy2(REF_SRC, REF)
    return REF if REF.exists() else None


def main():
    catalogo = json.loads((ROOT / "data" / "catalogo-lsm.json").read_text("utf-8"))
    por = {s["letra"]: s["pose"] for s in catalogo["senas"]}

    casos = {
        "00_catalogo": por["X"],
        "01_A": por["A"],
        "02_hook_recto": pose_x(),
        "03_hook_suave": pose_x(mcp=20, pip=55, dip=32),
        "04_hook_duro": pose_x(mcp=35, pip=82, dip=52),
        "05_curl45": pose_x(icurl=0.45, mcp=0, pip=0, dip=0),
        "06_y70": pose_x(wy=70),
        "07_y90": pose_x(wy=90),
        "08_z70": pose_x(wz=70),
        "09_z90": pose_x(wz=90),
        "10_y70_x-20": pose_x(wy=70, wx=-20),
        "11_y-70": pose_x(wy=-70),
        "12_z-70": pose_x(wz=-70),
        "13_y90_hookduro": pose_x(wy=90, mcp=35, pip=82, dip=52),
    }

    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 1000, "height": 1000})
        time.sleep(0.4)
        free_camera(page)

        ref = asegurar_ref()
        items = [("REF foto", ref)] if ref else []
        medidas = {}
        for nombre, pose in casos.items():
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
            time.sleep(0.28)
            m = page.evaluate(MEASURE_JS)
            medidas[nombre] = m
            if m.get("error"):
                print(" ", nombre, m)
                continue
            print(" ", linea(nombre, m))
            cam(page)
            ruta = OUT / f"{nombre}.png"
            captura(page, ruta, huesos=MANO, margen=0.42, lado=420)
            items.append((nombre, ruta))

        browser.close()

    hoja(items, OUT / "_hoja.png", cols=4, cell=360, titulo="X · forma y perfil")
    (OUT / "_medidas.json").write_text(
        json.dumps(medidas, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print("Hoja:", OUT / "_hoja.png")


if __name__ == "__main__":
    main()
