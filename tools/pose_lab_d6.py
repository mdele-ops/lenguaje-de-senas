"""Cierra dx/dy/dz a la vez para que las yemas se atravesen un poco."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_d6"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=d6"

T1 = "mixamorig1RightHandThumb1_036"
T2 = "mixamorig1RightHandThumb2_037"
T3 = "mixamorig1RightHandThumb3_038"

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


def pose(t2x, t1y=0, t1z=40, t3z=0, m_curl=0.58, t_curl=0.54, aside=0.38):
    extra = {T1: {"z": t1z}, T2: {"x": t2x}}
    if t1y:
        extra[T1]["y"] = t1y
    if t3z:
        extra[T3] = {"z": t3z}
    return {
        "thumb": {"curl": t_curl, "aside": aside},
        "index": {"curl": 0.0},
        "middle": {"curl": m_curl},
        "ring": {"curl": 0.92},
        "pinky": {"curl": 0.92},
        "extra": extra,
    }


CASES = {
    "00_ref": pose(-38),
    "01_y-4_x-34": pose(-34, t1y=-4),
    "02_y-5_x-36": pose(-36, t1y=-5),
    "03_y-6_x-34": pose(-34, t1y=-6),
    "04_y-6_x-36": pose(-36, t1y=-6),
    "05_y-3_x-38": pose(-38, t1y=-3),
    "06_y-4_x-38": pose(-38, t1y=-4),
    "07_y-5_x-38": pose(-38, t1y=-5),
    "08_y-4_x-36_z38": pose(-36, t1y=-4, t1z=38),
    "09_y-5_x-36_t3z8": pose(-36, t1y=-5, t3z=8),
    "10_y-5_x-36_t3z-8": pose(-36, t1y=-5, t3z=-8),
    "11_y-6_x-32": pose(-32, t1y=-6),
    "12_y-4_x-40": pose(-40, t1y=-4),
    "13_y-5_x-35_m56": pose(-35, t1y=-5, m_curl=0.56),
    "14_y-5_x-35_m60": pose(-35, t1y=-5, m_curl=0.60),
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
