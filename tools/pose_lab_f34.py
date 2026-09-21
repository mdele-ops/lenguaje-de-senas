"""F: circulo mas redondo + tres dedos un poco mas abiertos, sin clip."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_f34"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=f34ok"

T1 = "mixamorig1RightHandThumb1_036"
T2 = "mixamorig1RightHandThumb2_037"
I3 = "mixamorig1RightHandIndex3_042"

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
  if (scene.updateMatrixWorld) scene.updateMatrixWorld(true);
  const bones = {};
  scene.traverse((o) => { if (o && o.name) bones[o.name] = o; });
  function pos(name) {
    const b = bones[name];
    if (!b || !b.matrixWorld) return null;
    const e = b.matrixWorld.elements;
    return { x: e[12], y: e[13], z: e[14] };
  }
  const t1 = pos('mixamorig1RightHandThumb1_036');
  const t2 = pos('mixamorig1RightHandThumb2_037');
  const t3 = pos('mixamorig1RightHandThumb3_038');
  const t4 = pos('mixamorig1RightHandThumb4_039');
  const i2 = pos('mixamorig1RightHandIndex2_041');
  const i3 = pos('mixamorig1RightHandIndex3_042');
  const i4 = pos('mixamorig1RightHandIndex4_043');
  if (!t1 || !t4 || !i4) return { error: 'bones' };
  function dist(a, b) {
    const dx = a.x - b.x, dy = a.y - b.y, dz = a.z - b.z;
    return Math.sqrt(dx*dx + dy*dy + dz*dz);
  }
  const mid = { x: (t2.x+t3.x)/2, y: (t2.y+t3.y)/2, z: (t2.z+t3.z)/2 };
  const distTip = dist(t4, i4);
  const distShaft = Math.min(dist(i4, t2), dist(i4, t3), dist(i4, mid));
  const yemaToIndex = Math.min(dist(t4, i2), dist(t4, i3), dist(t4, i4));
  return {
    distTip, distShaft, yemaToIndex,
    wrap: distShaft + 0.001 < distTip * 0.55,
    clip: Math.min(yemaToIndex, distTip) < 0.038,
    touch: distTip >= 0.038 && distTip <= 0.072 && yemaToIndex >= 0.038,
    hole: distShaft >= 0.055 && distShaft <= 0.078 && distTip >= 0.038 && distTip <= 0.055
  };
}
"""


def pose(t_curl, aside, i_curl, t1z, t1y, t2x, spreads=(8, 10, 14), extra_i=None):
    extra = {T1: {"z": t1z, "y": t1y}, T2: {"x": t2x}}
    if extra_i:
        extra.update(extra_i)
    return {
        "thumb": {"curl": t_curl, "aside": aside},
        "index": {"curl": i_curl},
        "middle": {"curl": 0.0, "spread": spreads[0]},
        "ring": {"curl": 0.0, "spread": spreads[1]},
        "pinky": {"curl": 0.0, "spread": spreads[2]},
        "extra": extra,
    }


CASES = {
    "00_actual": {
        "thumb": {"curl": 0.38, "aside": 0.34},
        "index": {"curl": 0.42},
        "middle": {"curl": 0.0, "spread": 3},
        "ring": {"curl": 0.0, "spread": 4},
        "pinky": {"curl": 0.0, "spread": 6},
        "extra": {T1: {"z": 22, "y": -4}, T2: {"x": -20}},
    },
    "01_06": pose(0.46, 0.36, 0.48, 32, -5, -28),
    "02_open": pose(0.44, 0.36, 0.46, 30, -5, -24),
    "03_yema": pose(0.45, 0.36, 0.47, 30, -5, -26),
    "04_spread6": pose(0.45, 0.36, 0.47, 30, -5, -26, spreads=(6, 8, 12)),
    "05_i3hook": pose(
        0.44, 0.36, 0.44, 30, -5, -24, extra_i={I3: {"x": 10}}
    ),
    "06_round": pose(0.48, 0.38, 0.50, 28, -5, -26),
    "07_t2-22": pose(0.45, 0.35, 0.46, 28, -4, -22),
    "08_ilust": pose(0.46, 0.36, 0.48, 28, -5, -24, spreads=(7, 9, 13)),
}


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="chrome",
            args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"],
        )
        page = browser.new_page(viewport={"width": 1100, "height": 900})
        page.goto(URL, wait_until="networkidle")
        page.wait_for_selector("#anim-info", timeout=20000, state="attached")
        time.sleep(7)
        for _ in range(50):
            if page.evaluate(
                "() => window.__LSM_CONTROLLER__ && window.__LSM_CONTROLLER__.isModelReady()"
            ):
                break
            time.sleep(0.3)
        time.sleep(1.0)

        viewer = page.query_selector("#viewer")
        ranked = []
        for name, data in CASES.items():
            page.evaluate(
                "(pose) => window.__LSM_CONTROLLER__.applyTestPose(pose)", data
            )
            time.sleep(0.2)
            m = page.evaluate(MEASURE_JS)
            ranked.append((name, m))
            flags = []
            if m.get("hole"):
                flags.append("HOLE")
            if m.get("touch"):
                flags.append("TOUCH")
            if m.get("wrap"):
                flags.append("WRAP")
            if m.get("clip"):
                flags.append("CLIP")
            flag = " ".join(flags) or "far"
            print(
                f"{name}: tip={m['distTip']:.4f} yema={m['yemaToIndex']:.4f} "
                f"shaft={m['distShaft']:.4f} {flag}"
            )
            page.evaluate(
                """() => {
                    const mv = document.getElementById('handViewer');
                    mv.cameraTarget = '-0.30m 2.36m 0.20m';
                    mv.cameraOrbit = '0deg 72deg 0.48m';
                    mv.fieldOfView = '18deg';
                    mv.jumpCameraToGoal();
                }"""
            )
            time.sleep(0.14)
            viewer.screenshot(path=str(OUT_DIR / f"{name}_front.png"))
            page.evaluate(
                """() => {
                    const mv = document.getElementById('handViewer');
                    mv.cameraOrbit = '8deg 78deg 0.50m';
                    mv.jumpCameraToGoal();
                }"""
            )
            time.sleep(0.12)
            viewer.screenshot(path=str(OUT_DIR / f"{name}_hand.png"))

        print("ranked (hole, no wrap, no clip, touch):")
        scored = sorted(
            ranked,
            key=lambda x: (
                0 if x[1].get("hole") else 1,
                1 if x[1].get("wrap") else 0,
                1 if x[1].get("clip") else 0,
                0 if x[1].get("touch") else 1,
                abs(x[1]["distTip"] - 0.046),
                abs(x[1]["distShaft"] - 0.066),
            ),
        )
        for name, m in scored:
            flags = []
            if m.get("hole"):
                flags.append("HOLE")
            if m.get("touch"):
                flags.append("TOUCH")
            if m.get("wrap"):
                flags.append("WRAP")
            if m.get("clip"):
                flags.append("CLIP")
            flag = " ".join(flags) or "far"
            print(
                f"  {name}: tip={m['distTip']:.4f} shaft={m['distShaft']:.4f} {flag}"
            )
        browser.close()


if __name__ == "__main__":
    main()
