"""J lab 14: acercamiento a la mano durante la media luna (candidato F)."""
import json
import time
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_j14"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://127.0.0.1:8123/practica.html?v=j14"

FORE = "mixamorig1RightForeArm_034"

BASE = {
    "thumb": {"curl": 0.6},
    "index": {"curl": 0.95},
    "middle": {"curl": 0.95},
    "ring": {"curl": 0.95},
    "pinky": {"curl": 0.05},
    "muneca": {"y": -12},
}

KFS = [
    {"t": 0.00, "m": {"x": 0, "y": -12, "z": 0}, "f": 0},
    {"t": 0.15, "m": {"x": 3, "y": -12, "z": -14}, "f": 12},
    {"t": 0.30, "m": {"x": 5, "y": -12, "z": -16}, "f": 27},
    {"t": 0.45, "m": {"x": 6, "y": -12, "z": -4}, "f": 38},
    {"t": 0.60, "m": {"x": 5, "y": -13, "z": 20}, "f": 42},
    {"t": 0.75, "m": {"x": 3, "y": -14, "z": 46}, "f": 34},
    {"t": 0.88, "m": {"x": 1, "y": -15, "z": 68}, "f": 18},
    {"t": 1.00, "m": {"x": 0, "y": -16, "z": 84}, "f": 2},
]

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
  const b = bones['mixamorig1RightHand_035'];
  const e = b.matrixWorld.elements;
  return { x: e[12], y: e[13], z: e[14] };
}
"""


def lerp(a, b, u):
    return a + (b - a) * u


def sample(t):
    kfs = KFS
    if t <= kfs[0]["t"]:
        a = b = kfs[0]
        u = 0.0
    elif t >= kfs[-1]["t"]:
        a = b = kfs[-1]
        u = 0.0
    else:
        i = 0
        while i < len(kfs) - 2 and kfs[i + 1]["t"] < t:
            i += 1
        a, b = kfs[i], kfs[i + 1]
        u = (t - a["t"]) / ((b["t"] - a["t"]) or 1)
    pose = json.loads(json.dumps(BASE))
    pose["muneca"] = {k: lerp(a["m"][k], b["m"][k], u) for k in ("x", "y", "z")}
    pose["extra"] = {FORE: {"x": lerp(a["f"], b["f"], u)}}
    return pose


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="chrome",
            args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"],
        )
        page = browser.new_page(viewport={"width": 900, "height": 900})
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
        # Camara fija: si se mueve el target, model-viewer recentra la escena y
        # las medidas de huesos dejan de ser comparables entre cuadros.
        page.evaluate(
            """() => {
                const mv = document.getElementById('handViewer');
                mv.cameraTarget = '-0.38m 2.10m 0.20m';
                mv.cameraOrbit = '10deg 86deg 1.05m';
                mv.fieldOfView = '34deg';
                mv.jumpCameraToGoal();
            }"""
        )
        time.sleep(0.3)

        rutas = []
        for i in range(9):
            t = i / 8
            page.evaluate("(p) => window.__LSM_CONTROLLER__.applyTestPose(p)", sample(t))
            time.sleep(0.18)
            w = page.evaluate(MEASURE_JS)
            ruta = OUT_DIR / f"F_t{i}.png"
            viewer.screenshot(path=str(ruta))
            rutas.append(ruta)
            print(f"t={t:.2f} wrist=({w['x']:+.3f},{w['y']:+.3f},{w['z']:+.3f})", flush=True)

        ims = [Image.open(r) for r in rutas]
        tw = th = 300
        cols, filas = 3, 3
        hoja = Image.new("RGB", (tw * cols, th * filas), "white")
        for i, im in enumerate(ims):
            hoja.paste(im.resize((tw, th), Image.LANCZOS), ((i % cols) * tw, (i // cols) * th))
        hoja.save(OUT_DIR / "hoja_F.png")
        print("OK:", OUT_DIR, flush=True)
        browser.close()


if __name__ == "__main__":
    main()
