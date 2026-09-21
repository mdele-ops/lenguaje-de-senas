"""N lab 1: indice y medio hacia abajo sobre el pulgar; anular y menique cerrados."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_n"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=n1"

T1 = "mixamorig1RightHandThumb1_036"
ARM = "mixamorig1RightArm_033"

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
  function dir(a, b) {
    const dx = b.x - a.x, dy = b.y - a.y, dz = b.z - a.z;
    const len = Math.hypot(dx, dy, dz) || 1;
    return { x: dx / len, y: dy / len, z: dz / len };
  }
  const i1 = pos('mixamorig1RightHandIndex1_040');
  const i4 = pos('mixamorig1RightHandIndex4_043');
  const m4 = pos('mixamorig1RightHandMiddle4_047');
  const r4 = pos('mixamorig1RightHandRing4_051');
  const p4 = pos('mixamorig1RightHandPinky4_055');
  const t4 = pos('mixamorig1RightHandThumb4_039');
  const index = dir(i1, i4);
  return {
    idxDown: index.y,
    togIM: Math.hypot(i4.x - m4.x, i4.y - m4.y, i4.z - m4.z),
    ringBelow: r4.y < i4.y,
    pinkyBelow: p4.y < i4.y,
    iY: i4.y, mY: m4.y, rY: r4.y, pY: p4.y, tY: t4.y,
  };
}
"""


def n_pose(spread=8, x=148, extra=None, ic=0.04, mc=0.04, rc=0.95, pc=0.95):
    data = {
        "thumb": {"curl": 0.74, "aside": -0.5},
        "index": {"curl": ic, "spread": spread},
        "middle": {"curl": mc, "spread": -spread},
        "ring": {"curl": rc},
        "pinky": {"curl": pc},
        "muneca": {"x": x},
        "extra": {T1: {"y": -60, "x": -12}, ARM: {"z": -20}},
    }
    if extra:
        data["extra"].update(extra)
    return data


CASES = {
    "00_current": {
        "thumb": {"curl": 0.8, "twist": 8},
        "index": {"curl": 0.85},
        "middle": {"curl": 0.85},
        "ring": {"curl": 0.85},
        "pinky": {"curl": 0.85},
    },
    "01_m_like": n_pose(spread=8),
    "02_s0": n_pose(spread=0),
    "03_s12": n_pose(spread=12),
    "04_s16": n_pose(spread=16),
    "05_drape": n_pose(spread=8, ic=0.12, mc=0.12),
    "06_x140": n_pose(spread=8, x=140),
    "07_x155": n_pose(spread=8, x=155),
    "08_arm24": n_pose(spread=8, extra={ARM: {"z": -24}}),
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
        for name, data in CASES.items():
            page.evaluate(
                "(pose) => window.__LSM_CONTROLLER__.applyTestPose(pose)", data
            )
            time.sleep(0.25)
            m = page.evaluate(MEASURE_JS)
            if not m or m.get("error"):
                print(f"{name:14s}  ERROR {m}")
                continue
            print(
                f"{name:14s}  down={m['idxDown']:+.3f} togIM={m['togIM']:.3f} "
                f"ringBelow={m['ringBelow']} pinkyBelow={m['pinkyBelow']} "
                f"iY={m['iY']:+.3f} rY={m['rY']:+.3f} tY={m['tY']:+.3f}"
            )
            page.evaluate(
                """() => {
                    const mv = document.getElementById('handViewer');
                    mv.cameraTarget = '-0.22m 2.14m 0.22m';
                    mv.cameraOrbit = '-6deg 80deg 0.80m';
                    mv.fieldOfView = '20deg';
                    mv.jumpCameraToGoal();
                }"""
            )
            time.sleep(0.12)
            viewer.screenshot(path=str(OUT_DIR / f"{name}_frente.png"))
            page.evaluate(
                """() => {
                    const mv = document.getElementById('handViewer');
                    mv.cameraTarget = '-0.18m 2.20m 0.18m';
                    mv.cameraOrbit = '22deg 78deg 1.15m';
                    mv.fieldOfView = '22deg';
                    mv.jumpCameraToGoal();
                }"""
            )
            time.sleep(0.10)
            viewer.screenshot(path=str(OUT_DIR / f"{name}_mano.png"))

        browser.close()


if __name__ == "__main__":
    main()
