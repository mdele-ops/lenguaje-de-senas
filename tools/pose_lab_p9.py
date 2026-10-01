"""P lab 9: doblar la muñeca para copiar la inclinacion de la foto.

Midiendo la foto del usuario sobre una rejilla salen estos angulos en pantalla
(0 = horizontal a la derecha, 90 = hacia arriba):

    indice      ~51 grados
    dedo medio  ~-2 grados  (practicamente horizontal)
    escuadra    ~53 grados

Es decir: la escuadra de una mano real es de unos 55, no de 90 como en la
lamina dibujada, y ademas la mano va DOBLADA en la muñeca, inclinada en
diagonal. Con el nudillo del medio a 90 y la mano recta salia indice a 90 y
medio a 0: la letra correcta, pero tiesa y sin el doblez.

Aqui se baja el nudillo del medio a ~55 y se busca el doblez de muñeca que
gire el conjunto en el plano de la pantalla hasta dejar el medio horizontal,
sin perder el perfil (palmNz ~ 0) ni el largo aparente de los dedos.
"""
import itertools
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from pose_lab_e import ARM, BONES, _GET_SCENE
from pose_lab_p import REF
from pose_lab_p7 import CAM_FOV, CAM_ORBIT, CAM_TARGET, hoja
import search_e9 as se9
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "lab_p9"
OUT.mkdir(parents=True, exist_ok=True)

se9.URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=p9"

T1 = "mixamorig1RightHandThumb1_036"
T2 = "mixamorig1RightHandThumb2_037"

OBJETIVO = {"idxAng": 51.0, "midAng": -2.0}

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
  const norm = (v) => {
    const l = Math.hypot(v.x, v.y, v.z) || 1;
    return { x: v.x/l, y: v.y/l, z: v.z/l };
  };
  const cross = (a, b) => ({
    x: a.y*b.z - a.z*b.y, y: a.z*b.x - a.x*b.z, z: a.x*b.y - a.y*b.x,
  });
  const d = (a, b) => Math.hypot(a.x-b.x, a.y-b.y, a.z-b.z);
  // angulo en PANTALLA: la camara de produccion mira por el eje z, asi que la
  // pantalla es el plano x-y. 0 = a la derecha, 90 = hacia arriba.
  const ang = (a, b) => Math.atan2(b.y-a.y, b.x-a.x) * 180 / Math.PI;

  const wrist = P('mixamorig1RightHand_035');
  const fore = P('mixamorig1RightForeArm_034');
  const i1 = P('mixamorig1RightHandIndex1_040');
  const i4 = P('mixamorig1RightHandIndex4_043');
  const m1 = P('mixamorig1RightHandMiddle1_044');
  const m4 = P('mixamorig1RightHandMiddle4_047');
  const p1 = P('mixamorig1RightHandPinky1_052');
  const palm = d(wrist, i1) || 1;

  const nrm = norm(cross(sub(p1, i1), sub(m1, wrist)));
  const index = norm(sub(i4, i1));
  const middle = norm(sub(m4, m1));
  const dot = index.x*middle.x + index.y*middle.y + index.z*middle.z;

  return {
    idxAng: ang(i1, i4),
    midAng: ang(m1, m4),
    manoAng: ang(wrist, m1),        // eje de la mano
    brazoAng: ang(fore, wrist),     // eje del antebrazo
    palmNz: nrm.z,
    escuadra: Math.acos(Math.max(-1, Math.min(1, dot))) * 180 / Math.PI,
    idxScr: Math.hypot(i4.x-i1.x, i4.y-i1.y) / palm,
    midScr: Math.hypot(m4.x-m1.x, m4.y-m1.y) / palm,
  };
}
"""
)


def pose_p9(mid_mcp=55, wy=95, wz=12, wx=0, tcurl=0.85, taside=-0.3, t1y=-85,
            t2x=25, arm_z=-30, idx_spread=4):
    ex = {
        BONES["middle"][0]: {"x": mid_mcp},
        T1: {"y": t1y},
        T2: {"x": t2x},
        ARM: {"z": arm_z},
    }
    muneca = {k: v for k, v in (("x", wx), ("y", wy), ("z", wz)) if v}
    pose = {
        "thumb": {"curl": tcurl, "aside": taside},
        "index": {"curl": 0.0, "spread": idx_spread},
        "middle": {"curl": 0.0, "spread": -4},
        "ring": {"curl": 0.95},
        "pinky": {"curl": 0.95},
        "extra": ex,
    }
    if muneca:
        pose["muneca"] = muneca
    return pose


def banda(v, lo, hi):
    if v < lo:
        return lo - v
    if v > hi:
        return v - hi
    return 0.0


def puntuar(m):
    p = 0.0
    # los dos angulos de la foto son el objetivo principal
    p += 1.0 * abs(m["idxAng"] - OBJETIVO["idxAng"])
    p += 1.2 * abs(m["midAng"] - OBJETIVO["midAng"])
    # sin perder el perfil ni el largo aparente conseguidos antes
    p += 40.0 * banda(abs(m["palmNz"]), 0.0, 0.30)
    p += 30.0 * banda(m["midScr"], 0.80, 1.30)
    p += 30.0 * banda(m["idxScr"], 0.75, 1.30)
    return p


def main():
    rejilla = list(
        itertools.product(
            (45, 55, 65),                       # nudillo del medio
            (75, 85, 95, 105),                  # giro de muñeca
            (-30, -15, 0, 15, 30, 45),          # doblez z
            (-30, -15, 0, 15, 30),              # doblez x
        )
    )

    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 1100, "height": 900})
        time.sleep(0.5)
        viewer = page.query_selector("#viewer")
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
        time.sleep(0.4)

        res = []
        for mid_mcp, wy, wz, wx in rejilla:
            pose = pose_p9(mid_mcp=mid_mcp, wy=wy, wz=wz, wx=wx)
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
            m = page.evaluate(MEASURE_JS)
            res.append((puntuar(m), (mid_mcp, wy, wz, wx), m))
        res.sort(key=lambda t: t[0])

        print(f"{len(rejilla)} combinaciones. Objetivo de la foto: "
              f"idx={OBJETIVO['idxAng']} mid={OBJETIVO['midAng']}")
        for s, k, m in res[:14]:
            print(
                f"  mcp{k[0]:<3} wy{k[1]:<4} z{k[2]:<4} x{k[3]:<4} score={s:6.2f} "
                f"idx={m['idxAng']:+6.1f} mid={m['midAng']:+6.1f} "
                f"esc={m['escuadra']:5.1f} palmNz={m['palmNz']:+.2f} "
                f"scr={m['idxScr']:.2f}/{m['midScr']:.2f}"
            )

        items = [("REF foto", ROOT / "tools" / "screenshots" / "ref_P_zoom.png")]
        elegidos = {}
        for s, k, m in res[:8]:
            elegidos[f"mcp{k[0]}_wy{k[1]}_z{k[2]}_x{k[3]}"] = pose_p9(
                mid_mcp=k[0], wy=k[1], wz=k[2], wx=k[3]
            )
        for name, pose in elegidos.items():
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
            time.sleep(0.3)
            path = OUT / f"{name}.png"
            viewer.screenshot(path=str(path))
            items.append((name, path))

        browser.close()

    hoja(items, OUT / "_produccion.png", cols=3, cell=330, caja=(215, 65, 425, 275))
    (OUT / "_casos.json").write_text(json.dumps(elegidos, indent=2), "utf-8")


if __name__ == "__main__":
    main()
