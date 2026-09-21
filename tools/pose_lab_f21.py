"""F: pulgar vertical; el indice toca el MEDIO del pulgar; las yemas NO se pegan."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_f21"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=f21mid"

T1 = "mixamorig1RightHandThumb1_036"
I1 = "mixamorig1RightHandIndex1_040"
I2 = "mixamorig1RightHandIndex2_041"

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
  const t1 = pos('mixamorig1RightHandThumb1_036');
  const t2 = pos('mixamorig1RightHandThumb2_037');
  const t3 = pos('mixamorig1RightHandThumb3_038');
  const t4 = pos('mixamorig1RightHandThumb4_039');
  const i4 = pos('mixamorig1RightHandIndex4_043');
  if (!t1 || !t4 || !i4) return { error: 'bones' };
  function dist(a, b) {
    const dx = a.x - b.x, dy = a.y - b.y, dz = a.z - b.z;
    return Math.sqrt(dx*dx + dy*dy + dz*dz);
  }
  const mid = { x: (t2.x+t3.x)/2, y: (t2.y+t3.y)/2, z: (t2.z+t3.z)/2 };
  const tdx = t4.x - t1.x, tdy = t4.y - t1.y, tdz = t4.z - t1.z;
  const tlen = Math.sqrt(tdx*tdx + tdy*tdy + tdz*tdz) || 1;
  return {
    distMid: dist(i4, mid),
    distTip: dist(i4, t4),
    dx: i4.x - mid.x, dy: i4.y - mid.y, dz: i4.z - mid.z,
    thumbUp: tdy / tlen,
    tipsGlued: dist(i4, t4) < 0.025
  };
}
"""


def pose(i_curl, z=30, extra=None, i_spread=None):
    extra_data = {T1: {"z": z}}
    if extra:
        extra_data.update(extra)
    data = {
        "thumb": {"curl": 0.0},
        "index": {"curl": i_curl},
        "middle": {"curl": 0.0, "spread": 3},
        "ring": {"curl": 0.0, "spread": 4},
        "pinky": {"curl": 0.0, "spread": 6},
        "extra": extra_data,
    }
    if i_spread is not None:
        data["index"]["spread"] = i_spread
    return data


CASES = {
    "00_actual_tips": {
        "thumb": {"curl": 0.5, "aside": 0.3},
        "index": {"curl": 0.52},
        "middle": {"curl": 0.0, "spread": 3},
        "ring": {"curl": 0.0, "spread": 4},
        "pinky": {"curl": 0.0, "spread": 6},
        "extra": {T1: {"z": 22, "y": -4}, "mixamorig1RightHandThumb2_037": {"x": -36}},
    },
    "01_i62": pose(0.62),
    "02_i70": pose(0.70),
    "03_i74": pose(0.74),
    "04_i78": pose(0.78),
    "05_i70_s8": pose(0.70, i_spread=8),
    "06_i70_s-8": pose(0.70, i_spread=-8),
    "07_i74_s6": pose(0.74, i_spread=6),
    "08_i74_s-6": pose(0.74, i_spread=-6),
    "09_i70_i2x10": pose(0.70, extra={I2: {"x": 10}}),
    "10_i70_i2x-10": pose(0.70, extra={I2: {"x": -10}}),
    "11_i74_i2x8": pose(0.74, extra={I2: {"x": 8}}),
    "12_i74_i1x8": pose(0.74, extra={I1: {"x": 8}}),
    "13_i74_i1x-8": pose(0.74, extra={I1: {"x": -8}}),
    "14_z28_i74": pose(0.74, z=28),
    "15_z32_i74": pose(0.74, z=32),
}


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
        ranked = []
        for name, data in CASES.items():
            page.evaluate(
                "(pose) => window.__LSM_CONTROLLER__.applyTestPose(pose)", data
            )
            time.sleep(0.2)
            m = page.evaluate(MEASURE_JS)
            ranked.append((name, m))
            glued = "GLUED" if m["tipsGlued"] else "open"
            print(
                f"{name}: mid={m['distMid']:.4f} tip={m['distTip']:.4f} {glued} "
                f"up={m['thumbUp']:.3f} dx={m['dx']:+.3f} dy={m['dy']:+.3f} dz={m['dz']:+.3f}"
            )
            page.evaluate(
                """() => {
                    const mv = document.getElementById('handViewer');
                    mv.cameraTarget = '-0.30m 2.36m 0.20m';
                    mv.cameraOrbit = '8deg 78deg 0.50m';
                    mv.fieldOfView = '18deg';
                    mv.jumpCameraToGoal();
                }"""
            )
            time.sleep(0.14)
            viewer.screenshot(path=str(OUT_DIR / f"{name}_hand.png"))
            page.evaluate(
                """() => {
                    const mv = document.getElementById('handViewer');
                    mv.cameraOrbit = '12deg 76deg 0.40m';
                    mv.jumpCameraToGoal();
                }"""
            )
            time.sleep(0.12)
            viewer.screenshot(path=str(OUT_DIR / f"{name}_mid.png"))

        print("best: vertical + index at mid + tips not glued:")
        scored = sorted(
            ranked,
            key=lambda x: (
                1 if x[1]["tipsGlued"] else 0,
                1 if x[1]["thumbUp"] < 0.90 else 0,
                x[1]["distMid"] + abs(x[1]["dz"]) * 0.4,
            ),
        )
        for name, m in scored[:8]:
            glued = "GLUED" if m["tipsGlued"] else "open"
            print(
                f"  {name}: mid={m['distMid']:.4f} tip={m['distTip']:.4f} {glued} "
                f"up={m['thumbUp']:.3f} dz={m['dz']:+.3f}"
            )
        browser.close()


if __name__ == "__main__":
    main()
