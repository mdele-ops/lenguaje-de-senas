"""F: pulgar delante del indice, hueco, sin atravesar el fuste."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_f25"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=f25ord"

T1 = "mixamorig1RightHandThumb1_036"
I1 = "mixamorig1RightHandIndex1_040"
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
  const i4 = pos('mixamorig1RightHandIndex4_043');
  if (!t1 || !t4 || !i4) return { error: 'bones' };
  function dist(a, b) {
    const dx = a.x - b.x, dy = a.y - b.y, dz = a.z - b.z;
    return Math.sqrt(dx*dx + dy*dy + dz*dz);
  }
  const mid = { x: (t2.x+t3.x)/2, y: (t2.y+t3.y)/2, z: (t2.z+t3.z)/2 };
  const tdx = t4.x - t1.x, tdy = t4.y - t1.y, tdz = t4.z - t1.z;
  const tlen = Math.sqrt(tdx*tdx + tdy*tdy + tdz*tdz) || 1;
  const dz = i4.z - mid.z;
  return {
    distMid: dist(i4, mid),
    distShaft: Math.min(dist(i4, t2), dist(i4, t3), dist(i4, mid)),
    distTip: dist(i4, t4),
    dx: i4.x - mid.x, dy: i4.y - mid.y, dz,
    thumbUp: tdy / tlen,
    fused: Math.min(dist(i4, t2), dist(i4, t3), dist(i4, mid)) < 0.038,
    indexFront: dz > 0.008,
    thumbZ: mid.z, indexZ: i4.z
  };
}
"""


def pose(i_curl, extra=None, twist=None):
    extra_data = {T1: {"z": 30}, I2: {"z": -22}, I3: {"z": -26}}
    if extra:
        for name, rots in extra.items():
            if name in extra_data:
                merged = dict(extra_data[name])
                merged.update(rots)
                extra_data[name] = merged
            else:
                extra_data[name] = rots
    data = {
        "thumb": {"curl": 0.0},
        "index": {"curl": i_curl},
        "middle": {"curl": 0.0, "spread": 3},
        "ring": {"curl": 0.0, "spread": 4},
        "pinky": {"curl": 0.0, "spread": 6},
        "extra": extra_data,
    }
    if twist is not None:
        data["index"]["twist"] = twist
    return data


CASES = {
    "00_actual": pose(0.62),
    "01_t1x12": pose(0.62, {T1: {"z": 30, "x": 12}}),
    "02_t1x-12": pose(0.62, {T1: {"z": 30, "x": -12}}),
    "03_t1y12": pose(0.62, {T1: {"z": 30, "y": 12}}),
    "04_t1y-12": pose(0.62, {T1: {"z": 30, "y": -12}}),
    "05_i1y16": pose(0.62, {I1: {"y": 16}}),
    "06_i1y-16": pose(0.62, {I1: {"y": -16}}),
    "07_i1x24": pose(0.62, {I1: {"x": 24}}),
    "08_i1x-24": pose(0.62, {I1: {"x": -24}}),
    "09_tw12": pose(0.62, twist=12),
    "10_tw-12": pose(0.62, twist=-12),
    "11_i58_x48": pose(0.58, {I2: {"z": -22, "x": 48}}),
    "12_i55_x54": pose(0.55, {I2: {"z": -18, "x": 54}}),
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
            layer = "FRONT" if m["indexFront"] else "behind"
            fused = "FUSED" if m["fused"] else "gap"
            print(
                f"{name}: {layer} shaft={m['distShaft']:.4f} tip={m['distTip']:.4f} "
                f"{fused} up={m['thumbUp']:.3f} dz={m['dz']:+.3f} "
                f"tZ={m['thumbZ']:.3f} iZ={m['indexZ']:.3f}"
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
                    mv.cameraOrbit = '-35deg 80deg 0.50m';
                    mv.jumpCameraToGoal();
                }"""
            )
            time.sleep(0.12)
            viewer.screenshot(path=str(OUT_DIR / f"{name}_side.png"))

        print("best thumb-first with gap:")
        scored = sorted(
            ranked,
            key=lambda x: (
                1 if x[1]["indexFront"] else 0,
                1 if x[1]["fused"] else 0,
                1 if x[1]["thumbUp"] < 0.88 else 0,
                abs(x[1]["distShaft"] - 0.05),
            ),
        )
        for name, m in scored[:8]:
            layer = "FRONT" if m["indexFront"] else "behind"
            fused = "FUSED" if m["fused"] else "gap"
            print(
                f"  {name}: {layer} shaft={m['distShaft']:.4f} {fused} "
                f"up={m['thumbUp']:.3f} dz={m['dz']:+.3f}"
            )
        browser.close()


if __name__ == "__main__":
    main()
