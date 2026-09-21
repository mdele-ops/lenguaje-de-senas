"""W lab: indice, medio y anular arriba en tridente, meñique y pulgar recogidos.

La foto (W_usuario.png) pide:
  - palma de frente
  - indice, medio y anular estirados hacia arriba, separados un poco
    (tres palitos de la W, no un abanico abierto)
  - meñique recogido contra la palma
  - pulgar tumbado cruzando la palma, con la yema apoyada sobre el meñique

La W del catalogo usa spread +-40 (80 deg extra de indice a anular) y el
pulgar se queda de pie al costado. Este lab parte del pulgar de la U/V y
solo busca la abertura de los tres dedos largos.
"""
import json
import shutil
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from enfoque_r import MANO, captura, hoja
from pose_lab_e import T1, T2, _GET_SCENE, free_camera
from pose_lab_r import MEASURE_JS
from ver_s import CAM_FOV, CAM_ORBIT, CAM_TARGET
import search_e9 as se9
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "lab_w"
OUT.mkdir(parents=True, exist_ok=True)
REF_SRC = Path(
    r"C:\Users\KZTRDG\.cursor\projects"
    r"\c-Users-KZTRDG-General-Motors-Christian-Osvaldo-Partida-Cadena-Becarios-Manu-Lenguaje-de-se-as"
    r"\assets"
    r"\c__Users_KZTRDG_AppData_Roaming_Cursor_User_workspaceStorage"
    r"_e58e5485bac69e9b6ccd69cb178bd5da_images"
    r"\image-62298505-9f0f-4b8d-bc0a-ba50cb2c2c18.png"
)
REF = ROOT / "tools" / "screenshots" / "referencia" / "W_usuario.png"

se9.URL = "http://127.0.0.1:8006/practica.html?letra=%E2%97%8B&v=w1"

PULGAR_UV = {T1: {"y": -30, "z": 40}, T2: {"x": 60}}

# Angulos 3D y de pantalla entre las tres cadenas extendidas.
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
  const d = (a, b) => Math.hypot(a.x-b.x, a.y-b.y, a.z-b.z);
  const ang = (u, w) => {
    const c = Math.max(-1, Math.min(1, dot(u, w)));
    return Math.acos(c) * 180 / Math.PI;
  };

  const knuI = P('mixamorig1RightHandIndex1_040');
  const knuM = P('mixamorig1RightHandMiddle1_044');
  const knuR = P('mixamorig1RightHandRing1_048');
  const knuP = P('mixamorig1RightHandPinky1_052');
  const tipI = P('mixamorig1RightHandIndex4_043');
  const tipM = P('mixamorig1RightHandMiddle4_047');
  const tipR = P('mixamorig1RightHandRing4_051');
  const tipP = P('mixamorig1RightHandPinky4_055');
  const t4 = P('mixamorig1RightHandThumb4_039');
  const wrist = P('mixamorig1RightHand_035');
  const palm = d(wrist, knuI) || 1;

  const vI = norm(sub(tipI, knuI));
  const vM = norm(sub(tipM, knuM));
  const vR = norm(sub(tipR, knuR));

  const o = {
    angIM: ang(vI, vM),
    angMR: ang(vM, vR),
    angIR: ang(vI, vR),
    sepIM: d(tipI, tipM) / palm,
    sepMR: d(tipM, tipR) / palm,
    sepIR: d(tipI, tipR) / palm,
    altI: (tipI.y - knuI.y) / palm,
    altM: (tipM.y - knuM.y) / palm,
    altR: (tipR.y - knuR.y) / palm,
    pinkyFold: (knuP.y - tipP.y) / palm,
    thumbPinky: d(t4, tipP) / palm,
    angPxIM: null,
    angPxMR: null,
    angPxIR: null,
  };

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
    const dirPx = (knu, tip) => {
      const a = toPx(knu), b = toPx(tip);
      return { x: b.x - a.x, y: b.y - a.y };
    };
    const u = dirPx(knuI, tipI), w = dirPx(knuM, tipM), r = dirPx(knuR, tipR);
    const nrm = (v) => {
      const l = Math.hypot(v.x, v.y) || 1;
      return { x: v.x/l, y: v.y/l };
    };
    const nu = nrm(u), nw = nrm(w), nr = nrm(r);
    const ang2 = (a, b) => Math.acos(Math.max(-1, Math.min(1, a.x*b.x + a.y*b.y))) * 180 / Math.PI;
    o.angPxIM = ang2(nu, nw);
    o.angPxMR = ang2(nw, nr);
    o.angPxIR = ang2(nu, nr);
  }
  return o;
}
"""
)


def pose_w(iz=-14, mz=0, rz=14, tcurl=0.35, taside=-0.6, thumb=None, pcurl=0.95):
    """Tres dedos largos con spread; pulgar de la U/V sobre el meñique."""
    ex = dict(PULGAR_UV if thumb is None else thumb)
    return {
        "thumb": {"curl": tcurl, "aside": taside},
        "index": {"curl": 0.0, "spread": iz},
        "middle": {"curl": 0.0, "spread": mz},
        "ring": {"curl": 0.0, "spread": rz},
        "pinky": {"curl": pcurl},
        "extra": ex,
    }


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
    def fmt(v):
        return f"{v:5.1f}" if isinstance(v, (int, float)) else "  n/a"

    return (
        f"{nombre:22s} IM={a.get('angIM' ,0):5.1f}/{fmt(a.get('angPxIM'))} "
        f"MR={a.get('angMR', 0):5.1f}/{fmt(a.get('angPxMR'))} "
        f"IR={a.get('angIR', 0):5.1f}/{fmt(a.get('angPxIR'))} "
        f"sep={a.get('sepIM', 0):.2f}/{a.get('sepMR', 0):.2f} "
        f"thP={a.get('thumbPinky', 0):.2f} foldP={a.get('pinkyFold', 0):+.2f} "
        f"thLat={m.get('thLat', 0):+5.2f} thH={m.get('thHoriz', 0):.2f}"
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
        "00_W_catalogo": por["W"],
        "01_V": por["V"],
        "02_spread40_pulgarU": pose_w(iz=-40, rz=40),
        "03_z-10": pose_w(iz=-10, rz=10),
        "04_z-14": pose_w(iz=-14, rz=14),
        "05_z-18": pose_w(iz=-18, rz=18),
        "06_z-22": pose_w(iz=-22, rz=22),
        "07_z-26": pose_w(iz=-26, rz=26),
        "08_z-18_r22": pose_w(iz=-18, rz=22),
        "09_z-14_t50": pose_w(
            iz=-14, rz=14, thumb={T1: {"y": -30, "z": 50}, T2: {"x": 60}}
        ),
        "10_z-18_tcurl50": pose_w(iz=-18, rz=18, tcurl=0.5),
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

    hoja(items, OUT / "_hoja.png", cols=4, cell=320, titulo="W · lab 1 · tridente")
    (OUT / "_medidas.json").write_text(
        json.dumps(medidas, indent=2), encoding="utf-8"
    )
    print("Capturas en", OUT)


if __name__ == "__main__":
    main()
