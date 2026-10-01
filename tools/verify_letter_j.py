"""Verifica la letra J: media luna de muneca, tal como corre en produccion."""
import time
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "verify_j"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://127.0.0.1:8123/practica.html?v=jfinal"

# Camara fija sobre la mano derecha: moverla recentra la escena en model-viewer.
CAMARA_MANO = """() => {
    const mv = document.getElementById('handViewer');
    mv.cameraTarget = '-0.38m 2.10m 0.20m';
    mv.cameraOrbit = '10deg 86deg 1.05m';
    mv.fieldOfView = '34deg';
    mv.jumpCameraToGoal();
}"""

CAMARA_CUERPO = """() => {
    const mv = document.getElementById('handViewer');
    mv.cameraTarget = '0m 2.30m 0.15m';
    mv.cameraOrbit = '12deg 84deg 2.2m';
    mv.fieldOfView = '30deg';
    mv.jumpCameraToGoal();
}"""


MUESTREO_JS = """
(ms) => new Promise((resolve) => {
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
  const bones = {};
  scene.traverse((o) => { if (o && o.name) bones[o.name] = o; });
  const tip = bones['mixamorig1RightHandPinky4_055'];
  const wrist = bones['mixamorig1RightHand_035'];
  const out = [];
  const t0 = performance.now();
  function paso() {
    const e = tip.matrixWorld.elements;
    const w = wrist.matrixWorld.elements;
    out.push({
      ms: Math.round(performance.now() - t0),
      tip: { x: e[12], y: e[13], z: e[14] },
      wrist: { x: w[12], y: w[13], z: w[14] },
    });
    if (performance.now() - t0 >= ms) resolve(out);
    else requestAnimationFrame(paso);
  }
  requestAnimationFrame(paso);
})
"""


def dibuja_traza(puntos, nombre):
    from PIL import ImageDraw

    w = h = 560
    img = Image.new("RGB", (w, h), "white")
    d = ImageDraw.Draw(img)
    xs = [p["tip"]["x"] for p in puntos]
    ys = [p["tip"]["y"] for p in puntos]
    span = max(max(xs) - min(xs), max(ys) - min(ys), 1e-3) * 1.3
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2

    def proj(p):
        return (w / 2 + (p["x"] - cx) / span * w, h / 2 - (p["y"] - cy) / span * h)

    prev = None
    for i, p in enumerate(puntos):
        xy = proj(p["tip"])
        if prev:
            d.line([prev, xy], fill=(30, 90, 200), width=2)
        prev = xy
    d.ellipse([proj(puntos[0]["tip"])[0] - 6, proj(puntos[0]["tip"])[1] - 6,
               proj(puntos[0]["tip"])[0] + 6, proj(puntos[0]["tip"])[1] + 6], fill=(200, 30, 30))
    d.text((10, 10), nombre + "  (rojo = inicio)", fill=(0, 0, 0))
    img.save(OUT_DIR / f"{nombre}.png")


def hoja(nombre, rutas, cols=4):
    ims = [Image.open(r) for r in rutas]
    tw = th = 300
    filas = (len(ims) + cols - 1) // cols
    sheet = Image.new("RGB", (tw * cols, th * filas), "white")
    for i, im in enumerate(ims):
        sheet.paste(im.resize((tw, th), Image.LANCZOS), ((i % cols) * tw, (i // cols) * th))
    sheet.save(OUT_DIR / nombre)


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
        resultado = page.evaluate("() => window.__LSM_CONTROLLER__.mostrarSena('J')")
        print("modo:", resultado.get("modo"), flush=True)

        page.evaluate(CAMARA_MANO)
        # transicion 2 s + holdStart 0.6 s antes de que arranque el trazo
        time.sleep(2.6)

        muestras = page.evaluate(MUESTREO_JS, 1600)
        print(f"muestras: {len(muestras)}", flush=True)
        for m in muestras[:: max(1, len(muestras) // 10)]:
            t, w = m["tip"], m["wrist"]
            print(
                f"  {m['ms']:>5} ms  punta=({t['x']:+.3f},{t['y']:+.3f})"
                f"  muneca=({w['x']:+.3f},{w['y']:+.3f})",
                flush=True,
            )
        dibuja_traza(muestras, "traza_J_produccion")

        alto = max(m["tip"]["y"] for m in muestras)
        bajo = min(m["tip"]["y"] for m in muestras)
        izq = min(m["tip"]["x"] for m in muestras)
        der = max(m["tip"]["x"] for m in muestras)
        print(f"recorrido vertical: {alto - bajo:.3f} m", flush=True)
        print(f"recorrido lateral:  {der - izq:.3f} m", flush=True)

        # Congela el trazo en 5 instantes para revisar la mano de cerca.
        for etiqueta, espera in [
            ("00_inicio", 0.0),
            ("01_baja", 0.35),
            ("02_fondo", 0.35),
            ("03_gancho", 0.35),
            ("04_sube", 0.35),
        ]:
            time.sleep(espera)
            viewer.screenshot(path=str(OUT_DIR / f"J_{etiqueta}.png"))

        page.evaluate(CAMARA_CUERPO)
        time.sleep(0.5)
        viewer.screenshot(path=str(OUT_DIR / "J_cuerpo.png"))

        print("OK:", OUT_DIR, flush=True)
        browser.close()


if __name__ == "__main__":
    main()
