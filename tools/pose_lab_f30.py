"""F: yema del pulgar toca el indice, sin encimarse ni atravesar."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_f30"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=f30touch"

T1 = "mixamorig1RightHandThumb1_036"
T2 = "mixamorig1RightHandThumb2_037"
I2 = "mixamorig1RightHandIndex2_041"
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
  const tdx = t4.x - t1.x, tdy = t4.y - t1.y, tdz = t4.z - t1.z;
  const tlen = Math.sqrt(tdx*tdx + tdy*tdy + tdz*tdz) || 1;
  const distTip = dist(t4, i4);
  const distShaft = Math.min(dist(i4, t2), dist(i4, t3), dist(i4, mid));
  const yemaToIndex = Math.min(dist(t4, i2), dist(t4, i3), dist(t4, i4));
  return {
    distTip, distShaft, yemaToIndex,
    dx: i4.x - t4.x, dy: i4.y - t4.y, dz: i4.z - t4.z,
    thumbUp: tdy / tlen,
    wrap: distShaft + 0.001 < distTip * 0.55,
    fused: distShaft < 0.038 || yemaToIndex < 0.028,
    touching: yemaToIndex >= 0.032 && yemaToIndex <= 0.058 && distShaft > 0.040
  };
}
"""


def pose(i_curl, extra=None, t_curl=0.0, aside=None):
    thumb = {"curl": t_curl}
    if aside is not None:
        thumb["aside"] = aside
    return {
        "thumb": thumb,
        "index": {"curl": i_curl},
        "middle": {"curl": 0.0, "spread": 3},
        "ring": {"curl": 0.0, "spread": 4},
        "pinky": {"curl": 0.0, "spread": 6},
        "extra": extra or {},
    }


CASES = {
    "00_actual": pose(0.70, {T1: {"z": 30}, I2: {"x": 8}}),
    "01_i55": pose(0.55, {T1: {"z": 30}}),
    "02_i50": pose(0.50, {T1: {"z": 30}}),
    "03_i52_t2-18": pose(0.52, {T1: {"z": 30}, T2: {"x": -18}}),
    "04_i52_t2-28": pose(0.52, {T1: {"z": 30}, T2: {"x": -28}}),
    "05_f3": pose(
        0.52,
        {T1: {"z": 22, "y": -4}, T2: {"x": -36}},
        t_curl=0.50,
        aside=0.30,
    ),
    "06_i50_t2-22": pose(0.50, {T1: {"z": 30}, T2: {"x": -22}}),
    "07_i48_t2-24": pose(0.48, {T1: {"z": 30}, T2: {"x": -24}}),
    "08_i52_open": pose(0.52, {T1: {"z": 30}, I2: {"z": -14}, I3: {"z": -16}}),
    "09_i55_t2-16": pose(0.55, {T1: {"z": 30}, T2: {"x": -16}}),
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
            if m["touching"]:
                flags.append("TOUCH")
            if m["wrap"]:
                flags.append("WRAP")
            if m["fused"]:
                flags.append("FUSED")
            flag = " ".join(flags) or "gap"
            print(
                f"{name}: yema={m['yemaToIndex']:.4f} tip={m['distTip']:.4f} "
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

        print("best touch without wrap:")
        scored = sorted(
            ranked,
            key=lambda x: (
                1 if x[1]["wrap"] else 0,
                1 if x[1]["fused"] else 0,
                0 if x[1]["touching"] else 1,
                abs(x[1]["yemaToIndex"] - 0.045),
                1 if x[1]["thumbUp"] < 0.85 else 0,
            ),
        )
        for name, m in scored:
            flags = []
            if m["touching"]:
                flags.append("TOUCH")
            if m["wrap"]:
                flags.append("WRAP")
            if m["fused"]:
                flags.append("FUSED")
            flag = " ".join(flags) or "gap"
            print(
                f"  {name}: yema={m['yemaToIndex']:.4f} tip={m['distTip']:.4f} "
                f"shaft={m['distShaft']:.4f} {flag} up={m['thumbUp']:.3f}"
            )
        browser.close()


if __name__ == "__main__":
    main()
