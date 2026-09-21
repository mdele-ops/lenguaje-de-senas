"""Cierra el ultimo hueco de F y junta un poco los tres dedos altos."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_f3"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=f3"

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
  const index = pos('mixamorig1RightHandIndex4_043');
  if (!thumb || !index) return { error: 'bones' };
  const dx = thumb.x - index.x;
  const dy = thumb.y - index.y;
  const dz = thumb.z - index.z;
  return { dist: Math.sqrt(dx*dx+dy*dy+dz*dz), dx, dy, dz };
}
"""


def pose(t1y, t2x, t1z=22, t_curl=0.50, aside=0.30, i_curl=0.52, tight=False):
    data = {
        "thumb": {"curl": t_curl, "aside": aside},
        "index": {"curl": i_curl},
        "middle": {"curl": 0.0, "spread": -2} if tight else {"curl": 0.0},
        "ring": {"curl": 0.0, "spread": -3} if tight else {"curl": 0.0},
        "pinky": {"curl": 0.0, "spread": -5} if tight else {"curl": 0.0},
        "extra": {T1: {"z": t1z, "y": t1y}, T2: {"x": t2x}},
    }
    return data


CASES = {
    "00_ref": pose(-4, -36),
    "01_y-6": pose(-6, -36),
    "02_y-7": pose(-7, -36),
    "03_x-37": pose(-4, -37),
    "04_x-38": pose(-4, -38),
    "05_y-6_x-37": pose(-6, -37),
    "06_y-5_x-36": pose(-5, -36),
    "07_tight": pose(-4, -36, tight=True),
    "08_y-6_tight": pose(-6, -36, tight=True),
    "09_y-6_x-37_tight": pose(-6, -37, tight=True),
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
            ranked.append((name, m["dist"], m))
            print(
                f"{name}: dist={m['dist']:.4f} dx={m['dx']:+.4f} dy={m['dy']:+.4f} dz={m['dz']:+.4f}"
            )
            cam("-0.30m 2.36m 0.20m", "8deg 78deg 0.50m", "18deg")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_hand.png"))
            cam("-0.30m 2.36m 0.20m", "12deg 76deg 0.42m", "16deg")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_tips.png"))

        print("closest:")
        for name, dist, m in sorted(ranked, key=lambda x: x[1])[:6]:
            print(
                f"  {name}: {dist:.4f} dx={m['dx']:+.4f} dy={m['dy']:+.4f} dz={m['dz']:+.4f}"
            )
        browser.close()


if __name__ == "__main__":
    main()
