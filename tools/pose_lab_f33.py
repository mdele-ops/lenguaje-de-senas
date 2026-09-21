"""F: circulo pulgar-indice como la ilustracion (OK), tres dedos arriba."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_f33"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=f33ok"

T1 = "mixamorig1RightHandThumb1_036"
T2 = "mixamorig1RightHandThumb2_037"

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
  const tdx = t4.x - t1.x, tdy = t4.y - t1.y, tdz = t4.z - t1.z;
  const tlen = Math.sqrt(tdx*tdx + tdy*tdy + tdz*tdz) || 1;
  const distTip = dist(t4, i4);
  const distShaft = Math.min(dist(i4, t2), dist(i4, t3), dist(i4, mid));
  const yemaToIndex = Math.min(dist(t4, i2), dist(t4, i3), dist(t4, i4));
  return {
    distTip, distShaft, yemaToIndex,
    thumbUp: tdy / tlen,
    wrap: distShaft + 0.001 < distTip * 0.55,
    clip: Math.min(yemaToIndex, distTip) < 0.038,
    touch: distTip >= 0.038 && distTip <= 0.078 && yemaToIndex >= 0.038
  };
}
"""


def pose(t_curl, aside, i_curl, t1z, t1y, t2x, i_spread=None):
    index = {"curl": i_curl}
    if i_spread is not None:
        index["spread"] = i_spread
    return {
        "thumb": {"curl": t_curl, "aside": aside},
        "index": index,
        "middle": {"curl": 0.0, "spread": 8},
        "ring": {"curl": 0.0, "spread": 10},
        "pinky": {"curl": 0.0, "spread": 14},
        "extra": {T1: {"z": t1z, "y": t1y}, T2: {"x": t2x}},
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
    # Circulo tipo D (pulgar+medio) adaptado al indice
    "01_d_adapt": pose(0.54, 0.38, 0.56, 38, -5, -37),
    "02_d_z30": pose(0.54, 0.38, 0.56, 30, -5, -37),
    "03_d_z26": pose(0.54, 0.36, 0.54, 26, -5, -32),
    "04_curl50": pose(0.50, 0.36, 0.50, 30, -5, -32),
    "05_curl48_z28": pose(0.48, 0.34, 0.50, 28, -4, -30),
    "06_ok_abierto": pose(0.46, 0.36, 0.48, 32, -5, -28),
    "07_ok_cerrado": pose(0.52, 0.38, 0.54, 34, -5, -34),
    "08_i58_t48": pose(0.48, 0.34, 0.58, 28, -4, -28),
    "09_aside40_z32": pose(0.50, 0.40, 0.52, 32, -6, -30),
    "10_spread_i": pose(0.50, 0.36, 0.52, 30, -5, -30, i_spread=-6),
    "11_t2-24_z28": pose(0.46, 0.34, 0.48, 28, -4, -24),
    "12_classic": pose(0.50, 0.35, 0.52, 28, -5, -32),
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
            if m.get("touch"):
                flags.append("TOUCH")
            if m.get("wrap"):
                flags.append("WRAP")
            if m.get("clip"):
                flags.append("CLIP")
            flag = " ".join(flags) or "far"
            print(
                f"{name}: tip={m['distTip']:.4f} yema={m['yemaToIndex']:.4f} "
                f"shaft={m['distShaft']:.4f} {flag} up={m['thumbUp']:.3f}"
            )
            page.evaluate(
                """() => {
                    const mv = document.getElementById('handViewer');
                    mv.cameraTarget = '-0.30m 2.36m 0.20m';
                    mv.cameraOrbit = '8deg 78deg 0.50m';
                    mv.fieldOfView = '18deg';
                    mv.jumpCameraToGoal();
                }"""
            )
            time.sleep(0.14)
            viewer.screenshot(path=str(OUT_DIR / f"{name}_hand.png"))
            page.evaluate(
                """() => {
                    const mv = document.getElementById('handViewer');
                    mv.cameraOrbit = '-40deg 80deg 0.52m';
                    mv.jumpCameraToGoal();
                }"""
            )
            time.sleep(0.12)
            viewer.screenshot(path=str(OUT_DIR / f"{name}_side.png"))
            page.evaluate(
                """() => {
                    const mv = document.getElementById('handViewer');
                    mv.cameraOrbit = '0deg 72deg 0.48m';
                    mv.jumpCameraToGoal();
                }"""
            )
            time.sleep(0.12)
            viewer.screenshot(path=str(OUT_DIR / f"{name}_front.png"))

        print("ranked (no wrap, no clip, touch, tip~0.055):")
        scored = sorted(
            ranked,
            key=lambda x: (
                1 if x[1].get("wrap") else 0,
                1 if x[1].get("clip") else 0,
                0 if x[1].get("touch") else 1,
                abs(x[1]["distTip"] - 0.055),
            ),
        )
        for name, m in scored:
            flags = []
            if m.get("touch"):
                flags.append("TOUCH")
            if m.get("wrap"):
                flags.append("WRAP")
            if m.get("clip"):
                flags.append("CLIP")
            flag = " ".join(flags) or "far"
            print(
                f"  {name}: tip={m['distTip']:.4f} yema={m['yemaToIndex']:.4f} "
                f"shaft={m['distShaft']:.4f} {flag} up={m['thumbUp']:.3f}"
            )
        browser.close()


if __name__ == "__main__":
    main()
