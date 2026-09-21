"""Mide direccion del pulgar (punta vs base) para saber que rotacion lo sube."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
URL = "http://localhost:8123/practica.html?v=b6"

T1 = "mixamorig1RightHandThumb1_036"
T4 = "mixamorig1RightHandThumb4_039"

B = {
    "thumb": {"curl": 0.74, "aside": -0.5},
    "index": {"curl": 0.0, "spread": 14},
    "middle": {"curl": 0.0, "spread": 4},
    "ring": {"curl": 0.0, "spread": -10},
    "pinky": {"curl": 0.0, "spread": -20},
}

MEASURE_JS = """
() => {
  const bones = {};
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
  scene.traverse((o) => { if (o && o.name) bones[o.name] = o; });
  function pos(name) {
    const b = bones[name];
    if (!b) return null;
    const v = { x: 0, y: 0, z: 0 };
    if (b.getWorldPosition) {
      const t = b.getWorldPosition(b.position.clone ? b.position.clone() : { set: () => {}, x:0,y:0,z:0 });
      if (t && typeof t.x === 'number') return { x: t.x, y: t.y, z: t.z };
    }
    if (b.matrixWorld) {
      const e = b.matrixWorld.elements;
      return { x: e[12], y: e[13], z: e[14] };
    }
    return null;
  }
  const a = pos('mixamorig1RightHandThumb1_036');
  const b = pos('mixamorig1RightHandThumb4_039');
  if (!a || !b) return { error: 'bones', a, b, names: Object.keys(bones).filter(n => /Thumb/i.test(n)) };
  return {
    base: a,
    tip: b,
    dy: b.y - a.y,
    dx: b.x - a.x,
    dz: b.z - a.z,
  };
}
"""


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"]
        )
        page = browser.new_page(viewport={"width": 700, "height": 700})
        page.goto(URL, wait_until="networkidle")
        page.wait_for_selector("#anim-info", timeout=20000, state="attached")
        time.sleep(6)
        for _ in range(50):
            if page.evaluate(
                "() => window.__LSM_CONTROLLER__ && window.__LSM_CONTROLLER__.isModelReady()"
            ):
                break
            time.sleep(0.3)

        tests = [("actual_B", B)]
        for bone in [T1, "mixamorig1RightHandThumb2_037", "mixamorig1RightHandThumb3_038"]:
            short = bone.split("Thumb")[-1][:2]
            for axis in "xyz":
                for deg in (-90, -60, -30, 30, 60, 90, 120, 180):
                    pose = dict(B)
                    pose["extra"] = {bone: {axis: deg}}
                    tests.append((f"{short}_{axis}{deg:+d}", pose))

        # menos curl
        for curl in (0.0, 0.2, 0.4):
            pose = dict(B)
            pose["thumb"] = {"curl": curl, "aside": -0.5}
            tests.append((f"curl{curl}", pose))

        rows = []
        for name, pose in tests:
            page.evaluate(
                "(pose) => window.__LSM_CONTROLLER__.applyTestPose(pose)",
                pose,
            )
            time.sleep(0.12)
            m = page.evaluate(MEASURE_JS)
            dy = m.get("dy") if isinstance(m, dict) else None
            rows.append((name, m))
            print(f"{name:18} {m}")

        # top by dy (highest tip relative to base = most upward)
        valid = [(n, m) for n, m in rows if isinstance(m, dict) and "dy" in m]
        valid.sort(key=lambda t: t[1]["dy"], reverse=True)
        print("\n=== TOP dy (thumb tip above base) ===")
        for n, m in valid[:12]:
            print(f"{n:18} dy={m['dy']:.4f} dx={m['dx']:.4f} dz={m['dz']:.4f}")
        print("\n=== BOTTOM dy ===")
        for n, m in valid[-8:]:
            print(f"{n:18} dy={m['dy']:.4f} dx={m['dx']:.4f} dz={m['dz']:.4f}")

        browser.close()


if __name__ == "__main__":
    main()
