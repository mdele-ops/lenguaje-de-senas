"""Cierra el hueco: yemas de pulgar y medio deben chocar."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_d3"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=d3"

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
  return {
    dist: Math.sqrt(dx * dx + dy * dy + dz * dz),
    dx, dy, dz, thumb, middle
  };
}
"""


def pose(t_curl=0.54, aside=0.38, m_curl=0.58, extra=None):
    return {
        "thumb": {"curl": t_curl, "aside": aside},
        "index": {"curl": 0.0},
        "middle": {"curl": m_curl} if not isinstance(m_curl, dict) else m_curl,
        "ring": {"curl": 0.92},
        "pinky": {"curl": 0.92},
        "extra": extra or {T1: {"z": 40}, T2: {"x": -15}},
    }


CASES = {
    "00_actual": pose(),
    "01_t2x-28": pose(extra={T1: {"z": 40}, T2: {"x": -28}}),
    "02_t2x-35": pose(extra={T1: {"z": 42}, T2: {"x": -35}}),
    "03_z48_t2-28": pose(0.58, 0.40, 0.64, extra={T1: {"z": 48}, T2: {"x": -28}}),
    "04_z48_y-12": pose(0.58, 0.42, 0.64, extra={T1: {"z": 48, "y": -12}, T2: {"x": -22}}),
    "05_mid70": pose(0.58, 0.40, 0.70, extra={T1: {"z": 44}, T2: {"x": -22}}),
    "06_mid74_t62": pose(0.62, 0.42, 0.74, extra={T1: {"z": 46}, T2: {"x": -25}}),
    "07_t3x-20": pose(0.56, 0.40, 0.62, extra={T1: {"z": 42}, T2: {"x": -22}, T3: {"x": -20}}),
    "08_t3z-20": pose(0.56, 0.40, 0.62, extra={T1: {"z": 42}, T2: {"x": -22}, T3: {"z": -20}}),
    "09_t3z20": pose(0.56, 0.40, 0.62, extra={T1: {"z": 42}, T2: {"x": -22}, T3: {"z": 20}}),
    "10_m2x12": pose(0.56, 0.40, 0.62, extra={T1: {"z": 44}, T2: {"x": -24}, M2: {"x": 12}}),
    "11_m2x-12": pose(0.56, 0.40, 0.62, extra={T1: {"z": 44}, T2: {"x": -24}, M2: {"x": -12}}),
    "12_m2z12": pose(0.56, 0.40, 0.62, extra={T1: {"z": 44}, T2: {"x": -24}, M2: {"z": 12}}),
    "13_m2z-12": pose(0.56, 0.40, 0.62, extra={T1: {"z": 44}, T2: {"x": -24}, M2: {"z": -12}}),
    "14_push": pose(0.64, 0.46, 0.72, extra={T1: {"z": 50, "y": -10}, T2: {"x": -30}, T3: {"x": -12}}),
    "15_pinch": pose(0.60, 0.44, 0.68, extra={T1: {"z": 46, "y": -8}, T2: {"x": -26}, M2: {"x": 10}}),
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
            dist = m.get("dist") if isinstance(m, dict) else None
            ranked.append((name, dist, m))
            print(
                f"{name}: dist={dist:.4f} dx={m.get('dx'):+.4f} dy={m.get('dy'):+.4f} dz={m.get('dz'):+.4f}"
            )

            cam("-0.30m 2.36m 0.20m", "8deg 78deg 0.50m", "18deg")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_hand.png"))
            cam("-0.30m 2.36m 0.20m", "-40deg 80deg 0.55m", "20deg")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_palm.png"))

        print("closest:")
        for name, dist, m in sorted(
            [(n, d, mm) for n, d, mm in ranked if isinstance(d, (int, float))],
            key=lambda x: x[1],
        )[:8]:
            print(
                f"  {name}: {dist:.4f}  dx={m.get('dx'):+.4f} dy={m.get('dy'):+.4f} dz={m.get('dz'):+.4f}"
            )

        browser.close()


if __name__ == "__main__":
    main()
