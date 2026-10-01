"""J lab 13: afina la media luna (asta recta + gancho redondo que sube)."""
import json
import time
from pathlib import Path

from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_j13"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://127.0.0.1:8123/practica.html?v=j13"

FORE = "mixamorig1RightForeArm_034"

BASE = {
    "thumb": {"curl": 0.6},
    "index": {"curl": 0.95},
    "middle": {"curl": 0.95},
    "ring": {"curl": 0.95},
    "pinky": {"curl": 0.05},
    "muneca": {"y": -12},
}

CANDIDATOS = {
    "D_asta_recta": [
        {"t": 0.00, "m": {"x": 0, "y": -12, "z": 0}, "f": 0},
        {"t": 0.15, "m": {"x": 2, "y": -12, "z": 0}, "f": 13},
        {"t": 0.30, "m": {"x": 4, "y": -12, "z": 2}, "f": 26},
        {"t": 0.45, "m": {"x": 5, "y": -12, "z": 8}, "f": 37},
        {"t": 0.60, "m": {"x": 4, "y": -13, "z": 26}, "f": 40},
        {"t": 0.75, "m": {"x": 2, "y": -14, "z": 48}, "f": 33},
        {"t": 0.88, "m": {"x": 0, "y": -15, "z": 66}, "f": 20},
        {"t": 1.00, "m": {"x": 0, "y": -16, "z": 80}, "f": 6},
    ],
    "E_gancho_ancho": [
        {"t": 0.00, "m": {"x": 0, "y": -12, "z": 0}, "f": 0},
        {"t": 0.15, "m": {"x": 2, "y": -12, "z": -2}, "f": 14},
        {"t": 0.30, "m": {"x": 4, "y": -12, "z": 0}, "f": 28},
        {"t": 0.45, "m": {"x": 5, "y": -12, "z": 12}, "f": 40},
        {"t": 0.60, "m": {"x": 4, "y": -13, "z": 34}, "f": 42},
        {"t": 0.75, "m": {"x": 2, "y": -14, "z": 60}, "f": 34},
        {"t": 0.88, "m": {"x": 0, "y": -15, "z": 82}, "f": 18},
        {"t": 1.00, "m": {"x": 0, "y": -16, "z": 98}, "f": 0},
    ],
    "F_media_luna": [
        {"t": 0.00, "m": {"x": 0, "y": -12, "z": 0}, "f": 0},
        {"t": 0.15, "m": {"x": 3, "y": -12, "z": -14}, "f": 12},
        {"t": 0.30, "m": {"x": 5, "y": -12, "z": -16}, "f": 27},
        {"t": 0.45, "m": {"x": 6, "y": -12, "z": -4}, "f": 38},
        {"t": 0.60, "m": {"x": 5, "y": -13, "z": 20}, "f": 42},
        {"t": 0.75, "m": {"x": 3, "y": -14, "z": 46}, "f": 34},
        {"t": 0.88, "m": {"x": 1, "y": -15, "z": 68}, "f": 18},
        {"t": 1.00, "m": {"x": 0, "y": -16, "z": 84}, "f": 2},
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

ZOOM_JS = """() => {
    const mv = document.getElementById('handViewer');
    mv.cameraTarget = '0m 2.32m 0.15m';
    mv.cameraOrbit = '12deg 84deg 2.6m';
    mv.fieldOfView = '30deg';
    mv.jumpCameraToGoal();
}"""


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
    pose = json.loads(json.dumps(BASE))
    pose["muneca"] = {k: lerp(a["m"][k], b["m"][k], u) for k in ("x", "y", "z")}
    pose["extra"] = {FORE: {"x": lerp(a["f"], b["f"], u)}}
    return pose


def dibuja(nombre, puntos):
    w = h = 520
    img = Image.new("RGB", (w, h), "white")
    d = ImageDraw.Draw(img)
    xs = [p["x"] for p in puntos]
    ys = [p["y"] for p in puntos]
    span = max(max(xs) - min(xs), max(ys) - min(ys), 1e-3) * 1.3
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2

    def proj(p):
        return (w / 2 + (p["x"] - cx) / span * w, h / 2 - (p["y"] - cy) / span * h)

    prev = None
    for i, p in enumerate(puntos):
        xy = proj(p)
        if prev:
            d.line([prev, xy], fill=(30, 90, 200), width=3)
        prev = xy
        r = 6 if i in (0, len(puntos) - 1) else 3
        color = (
            (200, 30, 30)
            if i == 0
            else (20, 150, 60) if i == len(puntos) - 1 else (30, 90, 200)
        )
        d.ellipse([xy[0] - r, xy[1] - r, xy[0] + r, xy[1] + r], fill=color)
    d.text((10, 10), f"{nombre}  (rojo=inicio, verde=fin)", fill=(0, 0, 0))
    img.save(OUT_DIR / f"traza_{nombre}.png")


def contacto(nombre, archivos):
    ims = [Image.open(a) for a in archivos]
    w, h = ims[0].size
    esc = 0.42
    tw, th = int(w * esc), int(h * esc)
    hoja = Image.new("RGB", (tw * len(ims), th), "white")
    for i, im in enumerate(ims):
        hoja.paste(im.resize((tw, th), Image.LANCZOS), (i * tw, 0))
    hoja.save(OUT_DIR / f"tira_{nombre}.png")


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
            tiras = []
            print(f"== {nombre}", flush=True)
            for i in range(21):
                t = i / 20
                page.evaluate(
                    "(p) => window.__LSM_CONTROLLER__.applyTestPose(p)", sample(kfs, t)
                )
                time.sleep(0.12)
                m = page.evaluate(MEASURE_JS)
                puntos.append(m["tip"])
                if i % 5 == 0:
                    page.evaluate(ZOOM_JS)
                    time.sleep(0.08)
                    ruta = OUT_DIR / f"{nombre}_t{i:02d}.png"
                    viewer.screenshot(path=str(ruta))
                    tiras.append(str(ruta))
            for i, pt in enumerate(puntos):
                if i % 4 == 0:
                    print(
                        f"  t={i/20:.2f} tip=({pt['x']:+.3f},{pt['y']:+.3f},{pt['z']:+.3f})",
                        flush=True,
                    )
            dibuja(nombre, puntos)
            contacto(nombre, tiras)

        print("OK:", OUT_DIR, flush=True)
        browser.close()


if __name__ == "__main__":
    main()
