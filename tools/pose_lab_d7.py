"""Parte de 13 (yemas casi juntas) y cierra el hueco restante."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_d7"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=d7"

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
  const thumb = pos('mixamorig1RightHandThumb4_039');
  const middle = pos('mixamorig1RightHandMiddle4_047');
  if (!thumb || !middle) return { error: 'bones' };
  const dx = thumb.x - middle.x;
  const dy = thumb.y - middle.y;
  const dz = thumb.z - middle.z;
  return { dist: Math.sqrt(dx*dx+dy*dy+dz*dz), dx, dy, dz };
}
"""


def pose(t2x, t1y, t1z, m_curl, aside=0.38, t_curl=0.54):
    return {
        "thumb": {"curl": t_curl, "aside": aside},
        "index": {"curl": 0.0},
        "middle": {"curl": m_curl},
        "ring": {"curl": 0.92},
        "pinky": {"curl": 0.92},
        "extra": {T1: {"z": t1z, "y": t1y}, T2: {"x": t2x}},
    }


CASES = {
    "00_13": pose(-35, -5, 40, 0.56),
    "01_z38": pose(-35, -5, 38, 0.56),
    "02_z37": pose(-35, -5, 37, 0.56),
    "03_z38_x-36": pose(-36, -5, 38, 0.56),
    "04_z38_x-34": pose(-34, -5, 38, 0.56),
    "05_z38_m54": pose(-35, -5, 38, 0.54),
    "06_z38_m55": pose(-35, -5, 38, 0.55),
    "07_z38_m57": pose(-35, -5, 38, 0.57),
    "08_z38_y-4": pose(-35, -4, 38, 0.56),
    "09_z38_y-6": pose(-35, -6, 38, 0.56),
    "10_z38_as42": pose(-35, -5, 38, 0.56, aside=0.42),
    "11_z37_x-36_m55": pose(-36, -5, 37, 0.55),
    "12_z38_x-37_m56": pose(-37, -5, 38, 0.56),
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
            time.sleep(0.16)

        ranked = []
        for name, data in CASES.items():
            page.evaluate(
                "(pose) => window.__LSM_CONTROLLER__.applyTestPose(pose)", data
            )
            time.sleep(0.2)
            m = page.evaluate(MEASURE_JS)
            ranked.append((name, m["dist"], m, data))
            print(
                f"{name}: dist={m['dist']:.4f} dx={m['dx']:+.4f} dy={m['dy']:+.4f} dz={m['dz']:+.4f}"
            )
            cam("-0.30m 2.36m 0.20m", "-40deg 80deg 0.55m", "20deg")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_palm.png"))
            cam("-0.30m 2.36m 0.20m", "12deg 76deg 0.42m", "16deg")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_tips.png"))

        print("closest:")
        for name, dist, m, _ in sorted(ranked, key=lambda x: x[1])[:8]:
            print(
                f"  {name}: {dist:.4f} dx={m['dx']:+.4f} dy={m['dy']:+.4f} dz={m['dz']:+.4f}"
            )
        browser.close()


if __name__ == "__main__":
    main()
