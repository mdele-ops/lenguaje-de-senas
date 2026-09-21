"""J lab 11: mide a que direccion de pantalla mueve cada eje de la muneca.

Proyecta la punta del menique a coordenadas de pantalla para saber que
combinacion de x/y/z dibuja la media luna de la J vista de frente.
"""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_j11"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://127.0.0.1:8123/practica.html?v=j11"

BASE_FINGERS = {
    "thumb": {"curl": 0.6},
    "index": {"curl": 0.95},
    "middle": {"curl": 0.95},
    "ring": {"curl": 0.95},
    "pinky": {"curl": 0.05},
}

MEASURE_JS = """
() => {
  const mv = document.getElementById('handViewer');
  function getScene(m) {
    if (m.model && typeof m.model.traverse === 'function') return m.model;
    if (m.model && m.model.scene && typeof m.model.scene.traverse === 'function') return m.model.scene;
    const symbols = Object.getOwnPropertySymbols(m);
    for (let i = 0; i < symbols.length; i++) {
      const v = m[symbols[i]];
      if (v && typeof v.traverse === 'function') return v;
      if (v && v.model && typeof v.model.traverse === 'function') return v.model;
      if (v && v.target && typeof v.target.traverse === 'function') return v.target;
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
  const p1 = pos('mixamorig1RightHandPinky1_052');
  const p4 = pos('mixamorig1RightHandPinky4_055');
  const w = pos('mixamorig1RightHand_035');
  const dx = p4.x - p1.x, dy = p4.y - p1.y, dz = p4.z - p1.z;
  const len = Math.hypot(dx, dy, dz) || 1;
  return {
    tip: p4,
    wrist: w,
    dir: { x: dx / len, y: dy / len, z: dz / len },
  };
}
"""


def pose(muneca):
    data = dict(BASE_FINGERS)
    data["muneca"] = muneca
    return data


# Barrido de un eje a la vez, en ambos sentidos.
SEQ = {"base": {"x": 0, "y": 0, "z": 0}}
for axis in ("x", "y", "z"):
    for deg in (-60, -30, 30, 60):
        SEQ[f"{axis}{deg:+d}"] = {"x": 0, "y": 0, "z": 0, axis: deg}


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="chrome",
            args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"],
        )
        page = browser.new_page(viewport={"width": 1100, "height": 900})
        page.goto(URL, wait_until="networkidle")
        page.wait_for_selector("#anim-info", timeout=30000, state="attached")
        for _ in range(80):
            if page.evaluate(
                "() => window.__LSM_CONTROLLER__ && window.__LSM_CONTROLLER__.isModelReady()"
            ):
                break
            time.sleep(0.5)
        else:
            raise RuntimeError("El modelo 3D no cargo a tiempo")
        time.sleep(1.0)

        viewer = page.query_selector("#viewer")
        page.evaluate(
            "(p) => window.__LSM_CONTROLLER__.applyTestPose(p)", pose(SEQ["base"])
        )
        time.sleep(0.4)

        base = None
        for name, muneca in SEQ.items():
            page.evaluate(
                "(p) => window.__LSM_CONTROLLER__.applyTestPose(p)", pose(muneca)
            )
            time.sleep(0.2)
            m = page.evaluate(MEASURE_JS)
            t = m["tip"]
            if base is None:
                base = t
            d = m["dir"]
            print(
                f"{name:>6}  tip=({t['x']:+.3f},{t['y']:+.3f},{t['z']:+.3f})  "
                f"delta=({t['x']-base['x']:+.3f},{t['y']-base['y']:+.3f},{t['z']-base['z']:+.3f})  "
                f"dir=({d['x']:+.2f},{d['y']:+.2f},{d['z']:+.2f})",
                flush=True,
            )
            page.evaluate(
                """() => {
                    const mv = document.getElementById('handViewer');
                    mv.cameraTarget = '0m 2.40m 0.15m';
                    mv.cameraOrbit = '12deg 84deg 2.3m';
                    mv.fieldOfView = '30deg';
                    mv.jumpCameraToGoal();
                }"""
            )
            time.sleep(0.1)
            viewer.screenshot(path=str(OUT_DIR / f"{name}.png"))

        print("OK:", OUT_DIR, flush=True)
        browser.close()


if __name__ == "__main__":
    main()
