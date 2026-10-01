"""Diagnostico de proporciones de la mano en la letra H.

Mide, en metros de mundo, el ancho de nudillos, el largo de la palma y el de
cada dedo, con la pose del catalogo y variando `nudillos`, para ver cuanto
deforma la mano el apreton de nudillos.
"""
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "diag_h"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=diagh"

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
  function chain(p) {
    let t = 0;
    for (let i = 1; i <= 3; i++) t += d(p + i, p + (i + 1)) || 0;
    return t;
  }
  return {
    anchoNudillos: d('RightHandIndex1', 'RightHandPinky1'),
    nudIdxMid: d('RightHandIndex1', 'RightHandMiddle1'),
    nudMidRing: d('RightHandMiddle1', 'RightHandRing1'),
    nudRingPinky: d('RightHandRing1', 'RightHandPinky1'),
    palma: d('RightHand', 'RightHandMiddle1'),
    index: chain('RightHandIndex'),
    middle: chain('RightHandMiddle'),
    ring: chain('RightHandRing'),
    pinky: chain('RightHandPinky'),
    thumb: chain('RightHandThumb'),
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
    "dorso": {"orbit": "-70deg 80deg 0.7m", "fov": "28deg"},
    "arriba": {"orbit": "0deg 20deg 0.7m", "fov": "28deg"},
}


def fmt(m):
    return " ".join(
        f"{k}={(v * 100):.2f}cm" if isinstance(v, (int, float)) else f"{k}=?"
        for k, v in m.items()
    )


def main():
    catalogo = json.loads((ROOT / "data" / "catalogo-lsm.json").read_text("utf-8"))
    pose_h = next(s for s in catalogo["senas"] if s["letra"] == "H")["pose"]

    casos = {"H_catalogo": json.loads(json.dumps(pose_h))}
    for nud in (0.0, 0.2, 0.3, 0.45):
        p = json.loads(json.dumps(pose_h))
        p["nudillos"] = nud
        casos[f"H_nud{nud:.2f}"] = p
    casos["mano_abierta"] = {
        "thumb": {"curl": 0},
        "index": {"curl": 0},
        "middle": {"curl": 0},
        "ring": {"curl": 0},
        "pinky": {"curl": 0},
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(
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
            "(pose) => window.__LSM_CONTROLLER__.applyTestPose(pose)",
            casos["H_catalogo"],
        )
        time.sleep(0.6)

        viewer = page.query_selector("#viewer")
        for nombre, data in casos.items():
            page.evaluate(
                "(pose) => window.__LSM_CONTROLLER__.applyTestPose(pose)", data
            )
            time.sleep(0.35)
            print(f"{nombre}: {fmt(page.evaluate(MEASURE_JS))}")
            for vista, cam in VISTAS.items():
                page.evaluate(CAM_JS, cam)
                time.sleep(0.15)
                viewer.screenshot(path=str(OUT_DIR / f"{nombre}_{vista}.png"))

        browser.close()


if __name__ == "__main__":
    main()
