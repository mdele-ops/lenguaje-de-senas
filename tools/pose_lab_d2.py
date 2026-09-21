"""Afina la D ganadora: pulgar z+ para juntar yemas con el medio."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_d2"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=d2"

T1 = "mixamorig1RightHandThumb1_036"
T2 = "mixamorig1RightHandThumb2_037"
M1 = "mixamorig1RightHandMiddle1_044"

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
  return { dist: Math.sqrt(dx * dx + dy * dy + dz * dz) };
}
"""


def pose(thumb_curl, aside, mid_curl, z=30, extra=None, ring=0.92, pinky=0.92):
    extra_data = {T1: {"z": z}}
    if extra:
        extra_data.update(extra)
    return {
        "thumb": {"curl": thumb_curl, "aside": aside},
        "index": {"curl": 0.0},
        "middle": {"curl": mid_curl},
        "ring": {"curl": ring},
        "pinky": {"curl": pinky},
        "extra": extra_data,
    }


CASES = {
    "00_z30": pose(0.52, 0.36, 0.56, z=30),
    "01_z40": pose(0.52, 0.36, 0.56, z=40),
    "02_z50": pose(0.52, 0.36, 0.56, z=50),
    "03_z35_c58": pose(0.58, 0.38, 0.60, z=35),
    "04_z40_c60": pose(0.60, 0.40, 0.62, z=40),
    "05_z30_y-15": pose(0.52, 0.36, 0.56, z=30, extra={T1: {"z": 30, "y": -15}}),
    "06_z40_y-12": pose(0.54, 0.38, 0.58, z=40, extra={T1: {"z": 40, "y": -12}}),
    "07_z45_mid62": pose(0.55, 0.40, 0.62, z=45),
    "08_z40_t2x-15": pose(0.54, 0.38, 0.58, z=40, extra={T2: {"x": -15}}),
    "09_z42_m1x8": pose(0.56, 0.40, 0.58, z=42, extra={M1: {"x": 8}}),
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
            time.sleep(0.2)

        ranked = []
        for name, data in CASES.items():
            page.evaluate(
                "(pose) => window.__LSM_CONTROLLER__.applyTestPose(pose)", data
            )
            time.sleep(0.25)
            measure = page.evaluate(MEASURE_JS)
            dist = measure.get("dist") if isinstance(measure, dict) else None
            ranked.append((name, dist))
            print(f"{name}: dist={dist}")

            cam("-0.30m 2.36m 0.20m", "8deg 78deg 0.50m", "18deg")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_hand.png"))
            cam("-0.30m 2.36m 0.20m", "-40deg 80deg 0.55m", "20deg")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_palm.png"))
            cam("0m 2.45m 0.15m", "0deg 84deg 2.5m", "30deg")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_front.png"))

        print("closest:")
        for name, dist in sorted(
            [(n, d) for n, d in ranked if isinstance(d, (int, float))],
            key=lambda x: x[1],
        ):
            print(f"  {name}: {dist:.4f}")

        browser.close()


if __name__ == "__main__":
    main()
