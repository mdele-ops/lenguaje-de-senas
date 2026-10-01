"""O lab 2: cierra el circulo con extras de pulgar (como D) + orientacion de C."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_o2"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=o2"

ARM = "mixamorig1RightArm_033"
T1 = "mixamorig1RightHandThumb1_036"
T2 = "mixamorig1RightHandThumb2_037"
I1 = "mixamorig1RightHandIndex1_040"
M1 = "mixamorig1RightHandMiddle1_044"
R1 = "mixamorig1RightHandRing1_048"
P1 = "mixamorig1RightHandPinky1_052"

JUNTA = {"index": -4, "middle": 3, "ring": 4, "pinky": 6}

MEASURE_JS = """
() => {
  const mv = document.getElementById('handViewer');
  function getScene(modelViewer) {
    if (modelViewer.model && typeof modelViewer.model.traverse === 'function') return modelViewer.model;
    if (modelViewer.model && modelViewer.model.scene && typeof modelViewer.model.scene.traverse === 'function') return modelViewer.model.scene;
    const symbols = Object.getOwnPropertySymbols(modelViewer);
    for (let i = 0; i < symbols.length; i++) {
      const value = modelViewer[symbols[i]];
      if (value && typeof value.traverse === 'function') return value;
      if (value && value.model && typeof value.model.traverse === 'function') return value.model;
      if (value && value.target && typeof value.target.traverse === 'function') return value.target;
    }
    return null;
  }
  const scene = getScene(mv);
  if (!scene) return { error: 'no-scene' };
  if (scene.updateMatrixWorld) scene.updateMatrixWorld(true);
  const bones = {};
  scene.traverse((o) => { if (o && o.name) bones[o.name] = o; });
  function pos(name) {
    const b = bones[name];
    if (!b || !b.matrixWorld) return null;
    const e = b.matrixWorld.elements;
    return { x: e[12], y: e[13], z: e[14] };
  }
  function dist(a, b) {
    if (!a || !b) return null;
    return Math.hypot(a.x - b.x, a.y - b.y, a.z - b.z);
  }
  const t4 = pos('mixamorig1RightHandThumb4_039');
  const i4 = pos('mixamorig1RightHandIndex4_043');
  const m4 = pos('mixamorig1RightHandMiddle4_047');
  const r4 = pos('mixamorig1RightHandRing4_051');
  const p4 = pos('mixamorig1RightHandPinky4_055');
  const i2 = pos('mixamorig1RightHandIndex2_041');
  const t2 = pos('mixamorig1RightHandThumb2_037');
  return {
    dI: dist(t4, i4),
    dM: dist(t4, m4),
    dR: dist(t4, r4),
    dP: dist(t4, p4),
    hole: dist(i2, t2),
    dx: t4.x - i4.x,
    dy: t4.y - i4.y,
    dz: t4.z - i4.z,
  };
}
"""


def pose(curl, tcurl, taside, knuckle=12, ty=20, tz=0, t2x=0, muneca=None, arm=None):
    extra = {
        I1: {"x": knuckle},
        M1: {"x": knuckle},
        R1: {"x": knuckle},
        P1: {"x": knuckle},
        T1: {"y": ty, "z": tz},
        T2: {"x": t2x},
    }
    if arm:
        extra[ARM] = arm
    data = {
        "thumb": {"curl": tcurl, "aside": taside},
        "index": {"curl": curl, "spread": JUNTA["index"]},
        "middle": {"curl": curl, "spread": JUNTA["middle"]},
        "ring": {"curl": curl, "spread": JUNTA["ring"]},
        "pinky": {"curl": curl, "spread": JUNTA["pinky"]},
        "extra": extra,
    }
    if muneca:
        data["muneca"] = muneca
    return data


WRIST = {"y": 50}
ARMZ = {"z": -18}

CASES = {
    "00_current_wrist": {
        "thumb": {"curl": 0.55, "aside": 0.3},
        "index": {"curl": 0.6},
        "middle": {"curl": 0.6},
        "ring": {"curl": 0.6},
        "pinky": {"curl": 0.6},
        "muneca": WRIST,
        "extra": {ARM: ARMZ},
    },
    "01_cur_dthumb": {
        "thumb": {"curl": 0.55, "aside": 0.3},
        "index": {"curl": 0.6},
        "middle": {"curl": 0.6},
        "ring": {"curl": 0.6},
        "pinky": {"curl": 0.6},
        "muneca": WRIST,
        "extra": {ARM: ARMZ, T1: {"z": 38, "y": -5}, T2: {"x": -37}},
    },
    "02_c_dthumb": pose(0.40, 0.32, 0.74, ty=-5, tz=38, t2x=-37, muneca=WRIST, arm=ARMZ),
    "03_c52_d": pose(0.52, 0.42, 0.50, ty=-5, tz=38, t2x=-37, muneca=WRIST, arm=ARMZ),
    "04_c56_d": pose(0.56, 0.48, 0.40, ty=-5, tz=38, t2x=-37, muneca=WRIST, arm=ARMZ),
    "05_c50_tz28": pose(0.50, 0.46, 0.36, ty=0, tz=28, t2x=-28, muneca=WRIST, arm=ARMZ),
    "06_c50_tz20": pose(0.50, 0.46, 0.36, ty=8, tz=20, t2x=-20, muneca=WRIST, arm=ARMZ),
    "07_c48_tz32_t2-30": pose(0.48, 0.50, 0.32, ty=-2, tz=32, t2x=-30, muneca=WRIST, arm=ARMZ),
    "08_c46_as22": pose(0.46, 0.52, 0.22, ty=-5, tz=34, t2x=-32, muneca=WRIST, arm=ARMZ),
    "09_c58_as18": pose(0.58, 0.50, 0.18, ty=-5, tz=30, t2x=-28, muneca=WRIST, arm=ARMZ),
}


def wait_ready(page):
    time.sleep(8)
    for _ in range(80):
        try:
            if page.evaluate(
                "() => window.__LSM_CONTROLLER__ && window.__LSM_CONTROLLER__.isModelReady()"
            ):
                return
        except Exception:
            pass
        time.sleep(0.3)
    raise RuntimeError("El modelo 3D no cargo a tiempo")


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="chrome",
            args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"],
        )
        page = browser.new_page(viewport={"width": 1100, "height": 900})
        page.goto(URL, wait_until="networkidle")
        page.wait_for_selector("#anim-info", timeout=20000, state="attached")
        wait_ready(page)
        time.sleep(1.0)

        viewer = page.query_selector("#viewer")

        def cam(target, orbit, fov):
            page.evaluate(
                """(a) => {
                    const mv = document.getElementById('handViewer');
                    mv.cameraTarget = a.target;
                    mv.cameraOrbit = a.orbit;
                    mv.fieldOfView = a.fov;
                    mv.jumpCameraToGoal();
                }""",
                {"target": target, "orbit": orbit, "fov": fov},
            )
            time.sleep(0.15)

        for name, data in CASES.items():
            page.evaluate(
                "(pose) => window.__LSM_CONTROLLER__.applyTestPose(pose)", data
            )
            time.sleep(0.25)
            m = page.evaluate(MEASURE_JS)
            if not m or m.get("error"):
                print(f"{name:22s}  ERROR {m}")
                continue
            print(
                f"{name:22s}  dI={m['dI']:.3f} dM={m['dM']:.3f} "
                f"dR={m['dR']:.3f} dP={m['dP']:.3f} hole={m['hole']:.3f} "
                f"dxyz=({m['dx']:+.3f},{m['dy']:+.3f},{m['dz']:+.3f})"
            )
            cam("0m 2.40m 0.15m", "28deg 84deg 2.4m", "30deg")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_cuerpo.png"))
            cam("-0.30m 2.36m 0.20m", "8deg 78deg 0.50m", "18deg")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_perfil.png"))

        browser.close()


if __name__ == "__main__":
    main()
