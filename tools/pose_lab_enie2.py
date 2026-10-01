"""Ñ lab 2: amplitud del barrido lateral (hombro Y) con la cámara de la app."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_enie2"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=enie2"

ARM = "mixamorig1RightArm_033"

ENIE = {
    "thumb": {"curl": 0.74, "aside": -0.5},
    "index": {"curl": 0.12, "spread": 9},
    "middle": {"curl": 0.12, "spread": -3},
    "ring": {"curl": 0.95},
    "pinky": {"curl": 0.95},
    "muneca": {"x": 150, "y": 12},
    "extra": {
        "mixamorig1RightHandThumb1_036": {"y": -60, "x": -12},
        "mixamorig1RightHandRing1_048": {"x": 8},
        "mixamorig1RightHandRing2_049": {"x": 24},
        "mixamorig1RightHandRing3_050": {"x": 26},
        "mixamorig1RightHandPinky1_052": {"x": 8},
        "mixamorig1RightHandPinky2_053": {"x": 24},
        "mixamorig1RightHandPinky3_054": {"x": 26},
        ARM: {"z": -18},
    },
}

# +y aleja la mano hacia la izquierda del espectador, -y la trae a la derecha.
AMPLITUDES = [10, 14, 18]

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
  const tip = pos('mixamorig1RightHandIndex4_043');
  const hand = pos('mixamorig1RightHand_035');
  return { tip: tip, hand: hand };
}
"""


def merge_extra(patch):
    out = {k: dict(v) for k, v in ENIE["extra"].items()}
    for name, rots in patch.items():
        out[name] = dict(out.get(name, {}))
        out[name].update(rots)
    return out


def pose_arm_y(deg):
    data = {k: v for k, v in ENIE.items()}
    data["extra"] = merge_extra({ARM: {"y": deg, "z": -18}})
    return data


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
        # Cámara tal cual la sirve la app, sin tocarla entre muestras.
        page.evaluate(
            """() => {
                const mv = document.getElementById('handViewer');
                mv.cameraTarget = '0m 2.45m 0.15m';
                mv.cameraOrbit = '0deg 84deg 2.5m';
                mv.fieldOfView = '30deg';
                mv.jumpCameraToGoal();
            }"""
        )
        time.sleep(0.3)

        for amp in AMPLITUDES:
            print(f"--- amplitud +-{amp} deg ---")
            xs = []
            for i, frac in enumerate([1.0, 0.5, 0.0, -0.5, -1.0]):
                deg = amp * frac
                page.evaluate(
                    "(pose) => window.__LSM_CONTROLLER__.applyTestPose(pose)",
                    pose_arm_y(deg),
                )
                time.sleep(0.25)
                m = page.evaluate(MEASURE_JS)
                t, h = m["tip"], m["hand"]
                xs.append(t["x"])
                print(
                    f"  y={deg:+6.1f}  tip=({t['x']:+.3f},{t['y']:+.3f},{t['z']:+.3f})  "
                    f"mano=({h['x']:+.3f},{h['y']:+.3f},{h['z']:+.3f})"
                )
                viewer.screenshot(path=str(OUT_DIR / f"amp{amp}_{i}.png"))
            print(f"  recorrido lateral de la punta: {abs(xs[-1] - xs[0]) * 100:.1f} cm")

        browser.close()


if __name__ == "__main__":
    main()
