"""M lab 8: tres dedos colgando (volando) y muneca caida hacia el piso.

La version anterior los apretaba en puno sobre el pulgar. En LSM la M cuelga
indice/medio/anular hacia abajo; el pulgar sujeta el menique. Eso no se ve
con la muneca en reposo (dedos hacia arriba): hay que rotarla para que los
tres apunten al piso.
"""
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from pose_lab_e import ARM, HAND_POS_JS, T1, free_camera, set_cam
from pose_lab_m5 import hoja
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "lab_m8"
OUT.mkdir(parents=True, exist_ok=True)
REF = ROOT / "tools" / "screenshots" / "referencia" / "M_usuario.png"

import search_e9 as se9

se9.URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=m8"

FORE = "mixamorig1RightForeArm_034"

MEASURE_JS = """
() => {
  const mv = document.getElementById('handViewer');
  let scene = null;
  if (mv.model && typeof mv.model.traverse === 'function') scene = mv.model;
  else {
    for (const s of Object.getOwnPropertySymbols(mv)) {
      const v = mv[s];
      if (v && typeof v.traverse === 'function') { scene = v; break; }
      if (v && v.model && typeof v.model.traverse === 'function') { scene = v.model; break; }
    }
  }
  if (!scene) return { error: 'no-scene' };
  scene.updateMatrixWorld(true);
  const B = {};
  scene.traverse((o) => { if (o && o.name) B[o.name] = o; });
  const P = (n) => {
    const b = B[n];
    if (!b) return null;
    const e = b.matrixWorld.elements;
    return { x: e[12], y: e[13], z: e[14] };
  };
  const d = (a, b) => Math.hypot(a.x-b.x, a.y-b.y, a.z-b.z);
  const dir = (a, b) => {
    const x = b.x-a.x, y = b.y-a.y, z = b.z-a.z;
    const l = Math.hypot(x,y,z) || 1;
    return { x: x/l, y: y/l, z: z/l };
  };
  const i1 = P('mixamorig1RightHandIndex1_040');
  const i4 = P('mixamorig1RightHandIndex4_043');
  const m4 = P('mixamorig1RightHandMiddle4_047');
  const r4 = P('mixamorig1RightHandRing4_051');
  const wrist = P('mixamorig1RightHand_035');
  const index = dir(i1, i4);
  return {
    idxDown: index.y,
    idxFwd: index.z,
    togIM: d(i4, m4),
    togMR: d(m4, r4),
    hang: (i1.y - i4.y),
  };
}
"""


def pose(curl=0.04, spread=16, mx=150, my=0, mz=0, arm_z=-18, extra=None):
    data = {
        "thumb": {"curl": 0.74, "aside": -0.5},
        "index": {"curl": curl, "spread": spread},
        "middle": {"curl": curl},
        "ring": {"curl": curl, "spread": -spread},
        "pinky": {"curl": 0.95},
        "muneca": {"x": mx, "y": my, "z": mz},
        "extra": {T1: {"y": -60, "x": -12}, ARM: {"z": arm_z}},
    }
    if extra:
        data["extra"].update(extra)
    # quita ceros de muneca para no ensuciar
    data["muneca"] = {k: v for k, v in data["muneca"].items() if v}
    if not data["muneca"]:
        data.pop("muneca")
    return data


CAT = json.loads((ROOT / "data" / "catalogo-lsm.json").read_text("utf-8"))
CASES = {
    "00_actual": next(s for s in CAT["senas"] if s["letra"] == "M")["pose"],
    "A_x140": pose(mx=140),
    "B_x150": pose(mx=150),
    "C_x160": pose(mx=160),
    "D_x150_c12": pose(curl=0.12, mx=150),
    "E_x150_s10": pose(spread=10, mx=150),
    "F_x148_arm20": pose(mx=148, arm_z=-20),
    "G_x150_y12": pose(mx=150, my=12),
    "H_x150_z-12": pose(mx=150, mz=-12),
    "I_x80": pose(mx=80, curl=0.08),
    "J_x110": pose(mx=110, curl=0.08),
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

        for name, data in CASES.items():
            page.evaluate(
                "(pose) => window.__LSM_CONTROLLER__.applyTestPose(pose)", data
            )
            time.sleep(0.28)
            m = page.evaluate(MEASURE_JS)
            print(
                f"{name:14s} down={m['idxDown']:+.2f} fwd={m['idxFwd']:+.2f} "
                f"hang={m['hang']:+.3f} tog={m['togIM']:.3f}/{m['togMR']:.3f}"
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

    hoja(mano, OUT / "_mano.png", cols=3, cell=280)
    hoja(lado, OUT / "_lado.png", cols=3, cell=280)
    hoja(prod, OUT / "_prod.png", cols=3, cell=280)


if __name__ == "__main__":
    main()
