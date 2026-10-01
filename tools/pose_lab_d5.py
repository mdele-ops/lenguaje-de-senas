"""D: engancha la yema del medio hacia el pulgar para choque punta a punta."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_d5"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=d5"

T1 = "mixamorig1RightHandThumb1_036"
T2 = "mixamorig1RightHandThumb2_037"
T3 = "mixamorig1RightHandThumb3_038"
M1 = "mixamorig1RightHandMiddle1_044"
M2 = "mixamorig1RightHandMiddle2_045"
M3 = "mixamorig1RightHandMiddle3_046"

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
  const thumb = pos('mixamorig1RightHandThumb4_039');
  const middle = pos('mixamorig1RightHandMiddle4_047');
  if (!thumb || !middle) return { error: 'bones' };
  const dx = thumb.x - middle.x;
  const dy = thumb.y - middle.y;
  const dz = thumb.z - middle.z;
  return { dist: Math.sqrt(dx*dx+dy*dy+dz*dz), dx, dy, dz };
}
"""


def pose(m_curl, extra, t_curl=0.54, aside=0.38):
    return {
        "thumb": {"curl": t_curl, "aside": aside},
        "index": {"curl": 0.0},
        "middle": {"curl": m_curl},
        "ring": {"curl": 0.92},
        "pinky": {"curl": 0.92},
        "extra": extra,
    }


BASE = {T1: {"z": 40}, T2: {"x": -38}}

CASES = {
    "00_base38": pose(0.58, dict(BASE)),
    "01_m68": pose(0.68, dict(BASE)),
    "02_m74": pose(0.74, dict(BASE)),
    "03_m80": pose(0.80, dict(BASE)),
    "04_m68_m2x18": pose(0.68, {**BASE, M2: {"x": 18}}),
    "05_m68_m2x-18": pose(0.68, {**BASE, M2: {"x": -18}}),
    "06_m68_m2z18": pose(0.68, {**BASE, M2: {"z": 18}}),
    "07_m68_m2z-18": pose(0.68, {**BASE, M2: {"z": -18}}),
    "08_m70_m3x20": pose(0.70, {**BASE, M3: {"x": 20}}),
    "09_m70_m3x-20": pose(0.70, {**BASE, M3: {"x": -20}}),
    "10_m70_m3z20": pose(0.70, {**BASE, M3: {"z": 20}}),
    "11_m70_m3z-20": pose(0.70, {**BASE, M3: {"z": -20}}),
    "12_hook": pose(0.66, {**BASE, M2: {"x": 16}, M3: {"x": 18}}),
    "13_hook2": pose(0.64, {T1: {"z": 40}, T2: {"x": -34}, M2: {"x": 22}, M3: {"x": 16}}),
    "14_hook3": pose(0.62, {T1: {"z": 38}, T2: {"x": -30}, M1: {"x": 10}, M2: {"x": 20}, M3: {"x": 14}}),
    "15_meet": pose(0.72, {T1: {"z": 42}, T2: {"x": -32}, M2: {"x": 14}, M3: {"x": 12}}, t_curl=0.50, aside=0.42),
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
            time.sleep(0.18)

        ranked = []
        for name, data in CASES.items():
            page.evaluate(
                "(pose) => window.__LSM_CONTROLLER__.applyTestPose(pose)", data
            )
            time.sleep(0.22)
            m = page.evaluate(MEASURE_JS)
            ranked.append((name, m["dist"], m))
            print(
                f"{name}: dist={m['dist']:.4f} dx={m['dx']:+.4f} dy={m['dy']:+.4f} dz={m['dz']:+.4f}"
            )
            cam("-0.30m 2.36m 0.20m", "-40deg 80deg 0.55m", "20deg")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_palm.png"))
            cam("-0.30m 2.36m 0.20m", "8deg 78deg 0.50m", "18deg")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_hand.png"))

        print("closest:")
        for name, dist, m in sorted(ranked, key=lambda x: x[1])[:8]:
            print(
                f"  {name}: {dist:.4f} dx={m['dx']:+.4f} dy={m['dy']:+.4f} dz={m['dz']:+.4f}"
            )
        browser.close()


if __name__ == "__main__":
    main()
