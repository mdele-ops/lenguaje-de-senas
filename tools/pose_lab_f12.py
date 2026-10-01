"""Letra F correcta (referencia): palma al frente, pulgar e indice en circulo OK,
medio/anular/menique extendidos y un poco separados."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_f12"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=f12ok"

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


def pose(t_curl, aside, i_curl, extra=None, i_spread=None, up_spread=(3, 4, 6)):
    data = {
        "thumb": {"curl": t_curl, "aside": aside},
        "index": {"curl": i_curl},
        "middle": {"curl": 0.0, "spread": up_spread[0]},
        "ring": {"curl": 0.0, "spread": up_spread[1]},
        "pinky": {"curl": 0.0, "spread": up_spread[2]},
    }
    if i_spread is not None:
        data["index"]["spread"] = i_spread
    if extra:
        data["extra"] = extra
    return data


CASES = {
    "00_prod_cruz": {
        "thumb": {"curl": 0.05, "aside": 0.2},
        "index": {"curl": 0.75, "spread": 12},
        "middle": {"curl": 0.0, "spread": -2},
        "ring": {"curl": 0.0, "spread": -3},
        "pinky": {"curl": 0.0, "spread": -5},
        "extra": {T1: {"z": 90}},
    },
    "01_f3": pose(0.50, 0.30, 0.52, {T1: {"z": 22, "y": -4}, T2: {"x": -36}}),
    "02_f3_tight": pose(0.50, 0.30, 0.52, {T1: {"z": 22, "y": -4}, T2: {"x": -36}}, up_spread=(-2, -3, -5)),
    "03_d_on_index": pose(0.54, 0.38, 0.56, {T1: {"z": 38, "y": -5}, T2: {"x": -37}}),
    "04_d_soft": pose(0.50, 0.30, 0.52, {T1: {"z": 22, "y": -4}, T2: {"x": -20}}),
    "05_o_like": pose(0.55, 0.30, 0.60),
    "06_o_open": pose(0.48, 0.32, 0.50),
    "07_o_tight": pose(0.58, 0.36, 0.58),
    "08_z18_x-28": pose(0.52, 0.32, 0.54, {T1: {"z": 18, "y": -4}, T2: {"x": -28}}),
    "09_z12_x-24": pose(0.50, 0.28, 0.50, {T1: {"z": 12, "y": -2}, T2: {"x": -24}}),
    "10_z28_x-32": pose(0.52, 0.34, 0.54, {T1: {"z": 28, "y": -5}, T2: {"x": -32}}),
    "11_z22_x-36_i58": pose(0.50, 0.30, 0.58, {T1: {"z": 22, "y": -4}, T2: {"x": -36}}),
    "12_z22_x-36_t56": pose(0.56, 0.34, 0.52, {T1: {"z": 22, "y": -4}, T2: {"x": -36}}),
    "13_z22_as40": pose(0.50, 0.40, 0.52, {T1: {"z": 22, "y": -4}, T2: {"x": -36}}),
    "14_i_spread6": pose(0.50, 0.30, 0.52, {T1: {"z": 22, "y": -4}, T2: {"x": -36}}, i_spread=6),
    "15_i_spread-6": pose(0.50, 0.30, 0.52, {T1: {"z": 22, "y": -4}, T2: {"x": -36}}, i_spread=-6),
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
            ranked.append((name, m))
            print(
                f"{name}: dist={m['dist']:.4f} dx={m['dx']:+.4f} dy={m['dy']:+.4f} dz={m['dz']:+.4f}"
            )
            cam("-0.30m 2.36m 0.20m", "8deg 78deg 0.50m", "18deg")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_hand.png"))
            cam("-0.30m 2.36m 0.20m", "-40deg 80deg 0.55m", "20deg")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_palm.png"))
            cam("-0.30m 2.36m 0.20m", "12deg 76deg 0.42m", "16deg")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_tips.png"))

        print("closest:")
        for name, m in sorted(ranked, key=lambda x: x[1]["dist"])[:8]:
            print(
                f"  {name}: dist={m['dist']:.4f} dx={m['dx']:+.4f} dy={m['dy']:+.4f} dz={m['dz']:+.4f}"
            )
        browser.close()


if __name__ == "__main__":
    main()
