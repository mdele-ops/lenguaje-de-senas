"""Primeros planos de la mano en la H para comparar candidatos.

Encuadra solo la mano (target en el centro de la palma) desde cuatro angulos.
"""
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "cerca_h"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=cercah"

TARGET_JS = """
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
  const pts = ['RightHand','RightHandIndex4','RightHandMiddle4','RightHandThumb4','RightHandPinky1']
    .map(pos).filter(Boolean);
  const off = (scene.target && scene.target.position) || {x:0,y:0,z:0};
  let x=0,y=0,z=0;
  pts.forEach(p => { x+=p.x; y+=p.y; z+=p.z; });
  x = x/pts.length - (off.x||0);
  y = y/pts.length - (off.y||0);
  z = z/pts.length - (off.z||0);
  return x.toFixed(3)+'m '+y.toFixed(3)+'m '+z.toFixed(3)+'m';
}
"""

CAM_JS = """
(cam) => {
  const mv = document.getElementById('handViewer');
  mv.cameraTarget = cam.target;
  mv.cameraOrbit = cam.orbit;
  mv.fieldOfView = '26deg';
  mv.jumpCameraToGoal();
}
"""

ORBITAS = {
    "frente": "0deg 80deg 0.32m",
    "arriba": "0deg 18deg 0.32m",
    "dorso": "-75deg 80deg 0.32m",
    "punta": "80deg 78deg 0.32m",
}


def main():
    catalogo = json.loads((ROOT / "data" / "catalogo-lsm.json").read_text("utf-8"))
    base = next(s for s in catalogo["senas"] if s["letra"] == "H")["pose"]

    def variante(nud, isp, msp):
        p = json.loads(json.dumps(base))
        p["nudillos"] = nud
        p["index"]["spread"] = isp
        p["middle"]["spread"] = msp
        return p

    casos = {
        "00_actual": json.loads(json.dumps(base)),
        "01_n15_s15": variante(0.15, 15, -10),
        "02_n20_s13": variante(0.20, 13, -9),
        "03_n25_s12": variante(0.25, 12, -8),
    }

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            channel="chrome",
            args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"],
        )
        page = browser.new_page(viewport={"width": 1000, "height": 900})
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
            target = page.evaluate(TARGET_JS)
            for vista, orbit in ORBITAS.items():
                page.evaluate(CAM_JS, {"target": target, "orbit": orbit})
                time.sleep(0.18)
                viewer.screenshot(path=str(OUT_DIR / f"{nombre}_{vista}.png"))
            print(f"{nombre}: target={target}")

        browser.close()


if __name__ == "__main__":
    main()
