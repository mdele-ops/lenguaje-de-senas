"""J lab 12: traza la trayectoria de la punta del menique para el ciclo de la J.

Interpola los keyframes candidatos, mide la punta en el mundo y dibuja el
recorrido en un PNG (vista frontal) para comprobar que sea una media luna.
"""
import json
import time
from pathlib import Path

from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_j12"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://127.0.0.1:8123/practica.html?v=j12"

FORE = "mixamorig1RightForeArm_034"

BASE = {
    "thumb": {"curl": 0.6},
    "index": {"curl": 0.95},
    "middle": {"curl": 0.95},
    "ring": {"curl": 0.95},
    "pinky": {"curl": 0.05},
    "muneca": {"y": -12},
}

# Candidatos: (nombre, [ {t, muneca, fore} ... ])
CANDIDATOS = {
    "A_solo_muneca": [
        {"t": 0.0, "m": {"x": 0, "y": -12, "z": 0}, "f": 0},
        {"t": 0.3, "m": {"x": 0, "y": -12, "z": -35}, "f": 0},
        {"t": 0.6, "m": {"x": 0, "y": -12, "z": 0}, "f": 0},
        {"t": 1.0, "m": {"x": 0, "y": -12, "z": 55}, "f": 0},
    ],
    "B_baja_y_gancho": [
        {"t": 0.0, "m": {"x": 0, "y": -12, "z": 0}, "f": 0},
        {"t": 0.3, "m": {"x": 8, "y": -12, "z": -10}, "f": 26},
        {"t": 0.6, "m": {"x": 12, "y": -14, "z": 15}, "f": 40},
        {"t": 0.8, "m": {"x": 6, "y": -16, "z": 50}, "f": 30},
        {"t": 1.0, "m": {"x": 0, "y": -16, "z": 72}, "f": 10},
    ],
    "C_giro_amplio": [
        {"t": 0.0, "m": {"x": 0, "y": -12, "z": 0}, "f": 0},
        {"t": 0.25, "m": {"x": 10, "y": -12, "z": -25}, "f": 20},
        {"t": 0.5, "m": {"x": 16, "y": -14, "z": 20}, "f": 38},
        {"t": 0.75, "m": {"x": 8, "y": -16, "z": 70}, "f": 26},
        {"t": 1.0, "m": {"x": 0, "y": -16, "z": 100}, "f": 6},
    ],
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
    const e = b.matrixWorld.elements;
    return { x: e[12], y: e[13], z: e[14] };
  }
  return { tip: pos('mixamorig1RightHandPinky4_055'), wrist: pos('mixamorig1RightHand_035') };
}
"""


def lerp(a, b, u):
    return a + (b - a) * u


def sample(kfs, t):
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
    muneca = {k: lerp(a["m"][k], b["m"][k], u) for k in ("x", "y", "z")}
    fore = lerp(a["f"], b["f"], u)
    pose = json.loads(json.dumps(BASE))
    pose["muneca"] = muneca
    pose["extra"] = {FORE: {"x": fore}}
    return pose


def dibuja(nombre, puntos):
    """Vista frontal: X del mundo hacia la derecha, Y hacia arriba."""
    w = h = 520
    img = Image.new("RGB", (w, h), "white")
    d = ImageDraw.Draw(img)
    xs = [p["x"] for p in puntos]
    ys = [p["y"] for p in puntos]
    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)
    span = max(maxx - minx, maxy - miny, 1e-3) * 1.25
    cx, cy = (minx + maxx) / 2, (miny + maxy) / 2

    def proj(p):
        return (
            w / 2 + (p["x"] - cx) / span * w,
            h / 2 - (p["y"] - cy) / span * h,
        )

    prev = None
    for i, p in enumerate(puntos):
        xy = proj(p)
        if prev:
            d.line([prev, xy], fill=(30, 90, 200), width=3)
        prev = xy
        r = 5 if i in (0, len(puntos) - 1) else 3
        color = (200, 30, 30) if i == 0 else (20, 150, 60) if i == len(puntos) - 1 else (30, 90, 200)
        d.ellipse([xy[0] - r, xy[1] - r, xy[0] + r, xy[1] + r], fill=color)
    d.text((10, 10), f"{nombre}  (rojo=inicio, verde=fin)", fill=(0, 0, 0))
    img.save(OUT_DIR / f"traza_{nombre}.png")


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
        for nombre, kfs in CANDIDATOS.items():
            puntos = []
            print(f"== {nombre}", flush=True)
            for i in range(21):
                t = i / 20
                page.evaluate(
                    "(p) => window.__LSM_CONTROLLER__.applyTestPose(p)", sample(kfs, t)
                )
                time.sleep(0.12)
                m = page.evaluate(MEASURE_JS)
                puntos.append(m["tip"])
                if i % 4 == 0:
                    tp, wr = m["tip"], m["wrist"]
                    print(
                        f"  t={t:.2f} tip=({tp['x']:+.3f},{tp['y']:+.3f},{tp['z']:+.3f})"
                        f" wrist=({wr['x']:+.3f},{wr['y']:+.3f},{wr['z']:+.3f})",
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
                    time.sleep(0.08)
                    viewer.screenshot(path=str(OUT_DIR / f"{nombre}_t{i:02d}.png"))
            dibuja(nombre, puntos)

        print("OK:", OUT_DIR, flush=True)
        browser.close()


if __name__ == "__main__":
    main()
