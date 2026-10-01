"""V lab: indice y medio arriba en V estrecha, no en peace sign.

La foto (V_usuario.png) pide:
  - palma de frente
  - indice y medio estirados, abiertos unos 30-35 grados (las yemas se
    separan mas o menos el ancho de dos dedos, no el maximo)
  - anular y menique recogidos
  - pulgar tumbado sobre esos dos, sin montar en los dedos largos

La V del catalogo usa spread +-42: 84 grados de z extra encima del hueco
natural del rig, y se lee como una V de victoria muy abierta. Este lab
parte de la U (mismos pulgar y puno) y solo invierte el z para ABRIR,
buscando el angulo de pantalla de ~32 grados.
"""
import json
import shutil
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from enfoque_r import MANO, captura, hoja
from pose_lab_e import T1, T2, _GET_SCENE, free_camera
from pose_lab_r import MEASURE_JS
from pose_lab_u import pose_u
from ver_s import CAM_FOV, CAM_ORBIT, CAM_TARGET
import search_e9 as se9
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "lab_v"
OUT.mkdir(parents=True, exist_ok=True)
REF_SRC = Path(
    r"C:\Users\KZTRDG\.cursor\projects"
    r"\c-Users-KZTRDG-General-Motors-Christian-Osvaldo-Partida-Cadena-Becarios-Manu-Lenguaje-de-se-as"
    r"\assets"
    r"\c__Users_KZTRDG_AppData_Roaming_Cursor_User_workspaceStorage"
    r"_e58e5485bac69e9b6ccd69cb178bd5da_images"
    r"\image-92f5a572-9cb1-46b9-95c6-591107bac5ca.png"
)
REF = ROOT / "tools" / "screenshots" / "referencia" / "V_usuario.png"

se9.URL = "http://127.0.0.1:8006/practica.html?letra=%E2%97%8B&v=v1"

# Angulo 3D entre las cadenas indice/medio, mas el angulo proyectado en
# pantalla (lo que se ve en la foto). Se anade a las metricas de la R/U.
ANGLE_JS = (
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
  const norm = (v) => {
    const l = Math.hypot(v.x, v.y, v.z) || 1;
    return { x: v.x/l, y: v.y/l, z: v.z/l };
  };
  const knuI = P('mixamorig1RightHandIndex1_040');
  const knuM = P('mixamorig1RightHandMiddle1_044');
  const tipI = P('mixamorig1RightHandIndex4_043');
  const tipM = P('mixamorig1RightHandMiddle4_047');
  const vI = norm(sub(tipI, knuI));
  const vM = norm(sub(tipM, knuM));
  const c = Math.max(-1, Math.min(1, dot(vI, vM)));
  const ang3d = Math.acos(c) * 180 / Math.PI;

  let angPx = null;
  const symbols = Object.getOwnPropertySymbols(mv);
  let cam = null;
  for (let i = 0; i < symbols.length; i++) {
    const v = mv[symbols[i]];
    if (v && v.camera) { cam = v.camera; break; }
    if (v && v.target && v.target.camera) { cam = v.target.camera; break; }
  }
  if (cam) {
    cam.updateMatrixWorld(true);
    if (cam.updateProjectionMatrix) cam.updateProjectionMatrix();
    const mul = (e, p) => ({
      x: e[0]*p.x + e[4]*p.y + e[8]*p.z + e[12]*p.w,
      y: e[1]*p.x + e[5]*p.y + e[9]*p.z + e[13]*p.w,
      z: e[2]*p.x + e[6]*p.y + e[10]*p.z + e[14]*p.w,
      w: e[3]*p.x + e[7]*p.y + e[11]*p.z + e[15]*p.w,
    });
    const vi = cam.matrixWorldInverse.elements;
    const pr = cam.projectionMatrix.elements;
    const toPx = (p) => {
      const clip = mul(pr, mul(vi, { x: p.x, y: p.y, z: p.z, w: 1 }));
      return { x: clip.x / clip.w, y: clip.y / clip.w };
    };
    const a = toPx(knuI), b = toPx(tipI), c2 = toPx(knuM), d = toPx(tipM);
    const u = { x: b.x - a.x, y: b.y - a.y };
    const w = { x: d.x - c2.x, y: d.y - c2.y };
    const lu = Math.hypot(u.x, u.y) || 1;
    const lw = Math.hypot(w.x, w.y) || 1;
    const cd = Math.max(-1, Math.min(1, (u.x*w.x + u.y*w.y) / (lu * lw)));
    angPx = Math.acos(cd) * 180 / Math.PI;
  }
  return { ang3d, angPx };
}
"""
)


def pose_v(iz=-16, mz=16):
    """U con el z invertido: los dos dedos largos se abren en V."""
    return pose_u(iz=iz, mz=mz, arm_z=0)


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


def linea(nombre, m, a):
    ang = a.get("angPx")
    ang_txt = f"{ang:5.1f}" if isinstance(ang, (int, float)) else "  n/a"
    return (
        f"{nombre:22s} ang3d={a.get('ang3d', 0):5.1f} angPx={ang_txt} "
        f"yemas={m.get('sepYemas', 0):.3f} gap={m.get('gap', 0):.3f} "
        f"cruce={m.get('cruce', 0):+5.2f} thLat={m.get('thLat', 0):+5.2f}"
    )


def asegurar_ref():
    REF.parent.mkdir(parents=True, exist_ok=True)
    if REF_SRC.exists() and not REF.exists():
        shutil.copy2(REF_SRC, REF)
    return REF if REF.exists() else None


def main():
    catalogo = json.loads((ROOT / "data" / "catalogo-lsm.json").read_text("utf-8"))
    por = {s["letra"]: s["pose"] for s in catalogo["senas"]}

    casos = {
        "00_V_catalogo": por["V"],
        "01_U": por["U"],
        "02_z0": pose_v(iz=0, mz=0),
        "03_z-6": pose_v(iz=-6, mz=6),
        "04_z-10": pose_v(iz=-10, mz=10),
        "05_z-14": pose_v(iz=-14, mz=14),
        "06_z-18": pose_v(iz=-18, mz=18),
        "07_z-22": pose_v(iz=-22, mz=22),
        "08_z-26": pose_v(iz=-26, mz=26),
        "09_z-12_16": pose_v(iz=-12, mz=16),
        "10_spread-18": {
            "thumb": {"curl": 0.35, "aside": -0.6},
            "index": {"curl": 0.0, "spread": -18},
            "middle": {"curl": 0.0, "spread": 18},
            "ring": {"curl": 0.95},
            "pinky": {"curl": 0.95},
            "extra": {
                T1: {"y": -30, "z": 40},
                T2: {"x": 60},
            },
        },
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
            a = page.evaluate(ANGLE_JS)
            medidas[nombre] = {**m, **a}
            if m.get("error") or a.get("error"):
                print(" ", nombre, m, a)
                continue
            print(" ", linea(nombre, m, a))
            cam(page)
            ruta = OUT / f"{nombre}.png"
            captura(page, ruta, MANO, margen=0.28, lado=520)
            items.append((nombre, ruta))

        browser.close()

    hoja(items, OUT / "_hoja.png", cols=4, cell=320, titulo="V · lab 1 · angulo estrecho")
    (OUT / "_medidas.json").write_text(
        json.dumps(medidas, indent=2), encoding="utf-8"
    )
    print("Capturas en", OUT)


if __name__ == "__main__":
    main()
