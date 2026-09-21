"""N lab 3: la N es la M con dos dedos, no un puno.

En la lamina del usuario la N se ve igual que la M (dorso a la camara, muneca
caida y las yemas colgando hacia el piso) pero cuelgan solo indice y medio;
anular y menique quedan cerrados con el pulgar encima. Por eso aqui se parte
de la pose M aprobada (curl 0.12 + muneca x150 + brazo z-18) y se barre el
cierre del anular, el spread de los dos dedos y el angulo de muneca.
"""
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from pose_lab_e import ARM, BONES, HAND_POS_JS, T1, T2, T3, _GET_SCENE, free_camera, set_cam
from pose_lab_m5 import hoja
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "lab_n3"
OUT.mkdir(parents=True, exist_ok=True)
REF = ROOT / "tools" / "screenshots" / "referencia" / "N_usuario.png"

import search_e9 as se9

se9.URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=n3"

# idxDown/midDown: -1 = la yema apunta al piso (lo que pide la lamina).
# togIM: separacion indice-medio (van juntos, pero sin atravesarse).
# ringUp: cuanto queda la yema del anular POR ENCIMA de la del indice; es la
#         diferencia con la M, donde los tres cuelgan a la misma altura.
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
  const d = (a, b) => Math.hypot(a.x-b.x, a.y-b.y, a.z-b.z);
  const dir = (a, b) => {
    const x = b.x-a.x, y = b.y-a.y, z = b.z-a.z;
    const l = Math.hypot(x,y,z) || 1;
    return { x: x/l, y: y/l, z: z/l };
  };
  const wrist = P('mixamorig1RightHand_035');
  const i1 = P('mixamorig1RightHandIndex1_040');
  const i4 = P('mixamorig1RightHandIndex4_043');
  const m1 = P('mixamorig1RightHandMiddle1_044');
  const m4 = P('mixamorig1RightHandMiddle4_047');
  const r4 = P('mixamorig1RightHandRing4_051');
  const p4 = P('mixamorig1RightHandPinky4_055');
  const t4 = P('mixamorig1RightHandThumb4_039');
  const palm = d(wrist, i1) || 1;
  const index = dir(i1, i4);
  const middle = dir(m1, m4);
  return {
    idxDown: index.y,
    midDown: middle.y,
    togIM: d(i4, m4) / palm,
    ringUp: (r4.y - i4.y) / palm,
    pinkyUp: (p4.y - i4.y) / palm,
    thumbRing: d(t4, r4) / palm,
    hang: (i1.y - i4.y) / palm,
  };
}
"""
)


def pose_n(curl=0.12, spread=(10, -4), ring=0.95, pinky=0.95, mx=150, my=0, mz=0,
           tcurl=0.74, taside=-0.5, t1=None, t2x=0, t3x=0, arm_z=-18, extra=None):
    """Arma la N: indice y medio colgando, anular y menique cerrados."""
    ex = {ARM: {"z": arm_z}, T1: dict(t1 or {"y": -60, "x": -12})}
    if t2x:
        ex[T2] = {"x": t2x}
    if t3x:
        ex[T3] = {"x": t3x}
    if extra:
        for name, rot in extra.items():
            ex[name] = dict(ex.get(name, {}), **rot)
    data = {
        "thumb": {"curl": tcurl, "aside": taside},
        "index": {"curl": curl, "spread": spread[0]},
        "middle": {"curl": curl, "spread": spread[1]},
        "ring": {"curl": ring},
        "pinky": {"curl": pinky},
        "extra": ex,
    }
    muneca = {k: v for k, v in (("x", mx), ("y", my), ("z", mz)) if v}
    if muneca:
        data["muneca"] = muneca
    return data


CAT = json.loads((ROOT / "data" / "catalogo-lsm.json").read_text("utf-8"))
CASES = {
    "00_actual": next(s for s in CAT["senas"] if s["letra"] == "N")["pose"],
    "01_M": next(s for s in CAT["senas"] if s["letra"] == "M")["pose"],
    "A_base": pose_n(),
    "B_juntos": pose_n(spread=(6, -2)),
    "C_pegados": pose_n(spread=(3, 0)),
    "D_x140": pose_n(spread=(6, -2), mx=140),
    "E_x160": pose_n(spread=(6, -2), mx=160),
    "F_curl08": pose_n(curl=0.08, spread=(6, -2)),
    "G_curl18": pose_n(curl=0.18, spread=(6, -2)),
    "H_ring100": pose_n(spread=(6, -2), ring=1.0, pinky=1.0),
    "I_ring_pip": pose_n(
        spread=(6, -2),
        extra={
            BONES["ring"][1]: {"x": 16},
            BONES["ring"][2]: {"x": 20},
            BONES["pinky"][1]: {"x": 16},
            BONES["pinky"][2]: {"x": 20},
        },
    ),
    "J_pulgar_tapa": pose_n(spread=(6, -2), tcurl=0.62, taside=-0.34, t2x=22, t3x=14),
    "K_y12": pose_n(spread=(6, -2), my=12),
}


def main():
    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 900, "height": 950})
        time.sleep(0.3)
        viewer = page.query_selector("#viewer")
        free_camera(page)

        mano, lado, prod = [], [], []
        if REF.exists():
            mano.append(("REF foto", REF))
            lado.append(("REF foto", REF))

        for name, data in CASES.items():
            page.evaluate(
                "(pose) => window.__LSM_CONTROLLER__.applyTestPose(pose)", data
            )
            time.sleep(0.3)
            m = page.evaluate(MEASURE_JS)
            print(
                f"{name:14s} down={m['idxDown']:+.2f}/{m['midDown']:+.2f} "
                f"tog={m['togIM']:.2f} ringUp={m['ringUp']:+.2f} "
                f"pinkyUp={m['pinkyUp']:+.2f} hang={m['hang']:+.2f}"
            )
            hand = page.evaluate(HAND_POS_JS)
            set_cam(page, "mano", hand)
            p_m = OUT / f"{name}_mano.png"
            viewer.screenshot(path=str(p_m))
            mano.append((name, p_m))
            set_cam(page, "lado", hand)
            p_l = OUT / f"{name}_lado.png"
            viewer.screenshot(path=str(p_l))
            lado.append((name, p_l))
            set_cam(page, "prod", hand)
            p_p = OUT / f"{name}_prod.png"
            viewer.screenshot(path=str(p_p))
            prod.append((name, p_p))

        browser.close()

    hoja(mano, OUT / "_mano.png", cols=4, cell=280)
    hoja(lado, OUT / "_lado.png", cols=4, cell=280)
    hoja(prod, OUT / "_prod.png", cols=4, cell=280)
    (OUT / "_casos.json").write_text(json.dumps(CASES, indent=2), "utf-8")


if __name__ == "__main__":
    main()
