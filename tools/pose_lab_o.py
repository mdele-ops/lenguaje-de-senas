"""O lab 1: C cerrada — yemas juntas formando circulo, palma de perfil (LSM)."""
import shutil
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_o"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=o1"

REF_SRC = Path(
    r"C:\Users\KZTRDG\.cursor\projects\c-Users-KZTRDG-Documents-LENGUA-DE-SE-AS-PARTE-2"
    r"\assets\c__Users_KZTRDG_AppData_Roaming_Cursor_User_workspaceStorage_"
    r"918428176bcca0c3efb4b878bd61b4ca_images_image-450730a8-657b-4879-8012-8483471d45d5.png"
)
if REF_SRC.exists():
    shutil.copy(REF_SRC, OUT_DIR / "reference_o.png")

ARM = "mixamorig1RightArm_033"
T1 = "mixamorig1RightHandThumb1_036"
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
  const i1 = pos('mixamorig1RightHandIndex1_040');
  const t1 = pos('mixamorig1RightHandThumb1_036');
  return {
    dI: dist(t4, i4),
    dM: dist(t4, m4),
    dR: dist(t4, r4),
    dP: dist(t4, p4),
    hole: dist(i1, t1),
    iY: i4 && i4.y,
    tY: t4 && t4.y,
  };
}
"""


def pose(curl, thumb_curl, thumb_aside, thumb_y=20, knuckle=12, muneca=None, arm=None):
    extra = {
        I1: {"x": knuckle},
        M1: {"x": knuckle},
        R1: {"x": knuckle},
        P1: {"x": knuckle},
        T1: {"y": thumb_y},
    }
    if arm:
        extra[ARM] = arm
    data = {
        "thumb": {"curl": thumb_curl, "aside": thumb_aside},
        "index": {"curl": curl, "spread": JUNTA["index"]},
        "middle": {"curl": curl, "spread": JUNTA["middle"]},
        "ring": {"curl": curl, "spread": JUNTA["ring"]},
        "pinky": {"curl": curl, "spread": JUNTA["pinky"]},
        "extra": extra,
    }
    if muneca:
        data["muneca"] = muneca
    return data


CASES = {
    "00_current": {
        "thumb": {"curl": 0.55, "aside": 0.3},
        "index": {"curl": 0.6},
        "middle": {"curl": 0.6},
        "ring": {"curl": 0.6},
        "pinky": {"curl": 0.6},
    },
    "01_c_open": pose(0.40, 0.32, 0.74, muneca={"y": 50}, arm={"z": -18}),
    "02_c48_t38": pose(0.48, 0.38, 0.68, muneca={"y": 50}, arm={"z": -18}),
    "03_c52_t42": pose(0.52, 0.42, 0.62, muneca={"y": 50}, arm={"z": -18}),
    "04_c56_t46": pose(0.56, 0.46, 0.56, muneca={"y": 50}, arm={"z": -18}),
    "05_c60_t50": pose(0.60, 0.50, 0.48, muneca={"y": 50}, arm={"z": -18}),
    "06_c64_t54": pose(0.64, 0.54, 0.42, muneca={"y": 50}, arm={"z": -18}),
    "07_c58_t44_k18": pose(0.58, 0.44, 0.52, knuckle=18, muneca={"y": 50}, arm={"z": -18}),
    "08_c54_t48_ty8": pose(0.54, 0.48, 0.50, thumb_y=8, muneca={"y": 50}, arm={"z": -18}),
    "09_c54_t48_ty32": pose(0.54, 0.48, 0.50, thumb_y=32, muneca={"y": 50}, arm={"z": -18}),
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
                print(f"{name:20s}  ERROR {m}")
                continue
            print(
                f"{name:20s}  dI={m['dI']:.3f} dM={m['dM']:.3f} "
                f"dR={m['dR']:.3f} dP={m['dP']:.3f} hole={m['hole']:.3f}"
            )
            cam("0m 2.42m 0.12m", "22deg 84deg 2.4m", "30deg")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_body.png"))
            cam("-0.30m 2.36m 0.20m", "8deg 78deg 0.50m", "18deg")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_perfil.png"))
            cam("-0.22m 2.14m 0.22m", "-6deg 80deg 0.80m", "20deg")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_frente.png"))

        browser.close()


if __name__ == "__main__":
    main()
