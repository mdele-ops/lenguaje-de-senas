"""Barrido de la H: menos apreton de nudillos y mas aduccion por spread.

Busca la combinacion que deja indice y medio pegados sin encoger la palma:
mide el ancho de nudillos, la separacion entre las yemas de indice y medio y
la distancia entre las falanges medias de ambos dedos.
"""
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "barrido_h"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=barridoh"

MEASURE_JS = """
() => {
  const mv = document.getElementById('handViewer');
  function getScene(modelViewer) {
    if (modelViewer.model && typeof modelViewer.model.traverse === 'function') return modelViewer.model;
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
  function d(a, b) {
    const A = pos(a), B = pos(b);
    if (!A || !B) return null;
    return Math.hypot(A.x-B.x, A.y-B.y, A.z-B.z);
  }
  return {
    nudillos: d('RightHandIndex1', 'RightHandPinky1'),
    yemas: d('RightHandIndex4', 'RightHandMiddle4'),
    medias: d('RightHandIndex3', 'RightHandMiddle3'),
    bases: d('RightHandIndex2', 'RightHandMiddle2'),
  };
}
"""

CAM_JS = """
(cam) => {
  const mv = document.getElementById('handViewer');
  mv.cameraOrbit = cam.orbit;
  mv.fieldOfView = cam.fov;
  mv.jumpCameraToGoal();
}
"""

VISTAS = {
    "app": {"orbit": "0deg 78deg 0.75m", "fov": "30deg"},
    "arriba": {"orbit": "0deg 22deg 0.7m", "fov": "28deg"},
}


def main():
    catalogo = json.loads((ROOT / "data" / "catalogo-lsm.json").read_text("utf-8"))
    base = next(s for s in catalogo["senas"] if s["letra"] == "H")["pose"]

    casos = {"00_actual": json.loads(json.dumps(base))}
    for nud in (0.15, 0.25, 0.35):
        for isp, msp in ((10, -5), (15, -10), (20, -14)):
            p = json.loads(json.dumps(base))
            p["nudillos"] = nud
            p["index"]["spread"] = isp
            p["middle"]["spread"] = msp
            casos[f"n{int(nud*100):02d}_s{isp}_{msp}"] = p

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            channel="chrome",
            args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"],
        )
        page = browser.new_page(viewport={"width": 1100, "height": 900})
        page.goto(URL, wait_until="networkidle")
        page.wait_for_selector("#anim-info", timeout=20000, state="attached")
        for _ in range(80):
            if page.evaluate(
                "() => window.__LSM_CONTROLLER__ && window.__LSM_CONTROLLER__.isModelReady()"
            ):
                break
            time.sleep(0.3)
        time.sleep(2.0)

        page.evaluate(
            "(pose) => window.__LSM_CONTROLLER__.applyTestPose(pose)", casos["00_actual"]
        )
        time.sleep(0.6)

        viewer = page.query_selector("#viewer")
        for nombre, data in casos.items():
            page.evaluate(
                "(pose) => window.__LSM_CONTROLLER__.applyTestPose(pose)", data
            )
            time.sleep(0.35)
            m = page.evaluate(MEASURE_JS)
            print(
                f"{nombre}: nudillos={m['nudillos']*100:.2f}cm "
                f"bases={m['bases']*100:.2f}cm medias={m['medias']*100:.2f}cm "
                f"yemas={m['yemas']*100:.2f}cm"
            )
            for vista, cam in VISTAS.items():
                page.evaluate(CAM_JS, cam)
                time.sleep(0.15)
                viewer.screenshot(path=str(OUT_DIR / f"{nombre}_{vista}.png"))

        browser.close()


if __name__ == "__main__":
    main()
