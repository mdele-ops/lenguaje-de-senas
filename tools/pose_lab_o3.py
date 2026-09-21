"""O lab 3: parte de 05 y junta anular/menique al circulo."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_o3"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=o3"

ARM = "mixamorig1RightArm_033"
T1 = "mixamorig1RightHandThumb1_036"
T2 = "mixamorig1RightHandThumb2_037"
I1 = "mixamorig1RightHandIndex1_040"
M1 = "mixamorig1RightHandMiddle1_044"
R1 = "mixamorig1RightHandRing1_048"
P1 = "mixamorig1RightHandPinky1_052"

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
    dI: dist(t4, i4), dM: dist(t4, m4), dR: dist(t4, r4), dP: dist(t4, p4),
    hole: dist(i2, t2),
  };
}
"""


def pose(ic=0.50, mc=0.50, rc=0.50, pc=0.50, pk=12, rk=12, tz=28, t2x=-28, taside=0.36):
    return {
        "thumb": {"curl": 0.46, "aside": taside},
        "index": {"curl": ic, "spread": -4},
        "middle": {"curl": mc, "spread": 3},
        "ring": {"curl": rc, "spread": 4},
        "pinky": {"curl": pc, "spread": 6},
        "muneca": {"y": 50},
        "extra": {
            I1: {"x": 12},
            M1: {"x": 12},
            R1: {"x": rk},
            P1: {"x": pk},
            T1: {"y": 0, "z": tz},
            T2: {"x": t2x},
            ARM: {"z": -18},
        },
    }


CASES = {
    "00_05": pose(),
    "01_r58_p62": pose(rc=0.58, pc=0.62),
    "02_r62_p68": pose(rc=0.62, pc=0.68),
    "03_r66_p72": pose(rc=0.66, pc=0.72),
    "04_pk20": pose(pk=20, rk=16),
    "05_r60_pk22": pose(rc=0.60, pc=0.66, pk=22, rk=16),
    "06_all52": pose(ic=0.52, mc=0.52, rc=0.58, pc=0.64),
    "07_tz30_r60": pose(rc=0.60, pc=0.66, tz=30, t2x=-30),
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
            print(
                f"{name:16s}  dI={m['dI']:.3f} dM={m['dM']:.3f} "
                f"dR={m['dR']:.3f} dP={m['dP']:.3f} hole={m['hole']:.3f}"
            )
            cam("-0.30m 2.36m 0.20m", "8deg 78deg 0.50m", "18deg")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_perfil.png"))
            cam("0m 2.40m 0.15m", "28deg 84deg 2.4m", "30deg")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_cuerpo.png"))

        browser.close()


if __name__ == "__main__":
    main()
