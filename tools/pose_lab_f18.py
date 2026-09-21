"""F: yemas se tocan sin entrelazarse. El indice no debe pasar detras del pulgar."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_f18"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=f18t"

T1 = "mixamorig1RightHandThumb1_036"
T2 = "mixamorig1RightHandThumb2_037"
T3 = "mixamorig1RightHandThumb3_038"
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
  const tdx = t4.x - t1.x, tdy = t4.y - t1.y, tdz = t4.z - t1.z;
  const tlen = Math.sqrt(tdx*tdx + tdy*tdy + tdz*tdz) || 1;
  function dist(a, b) {
    const dx = a.x - b.x, dy = a.y - b.y, dz = a.z - b.z;
    return Math.sqrt(dx*dx + dy*dy + dz*dz);
  }
  const mid = { x: (t2.x+t3.x)/2, y: (t2.y+t3.y)/2, z: (t2.z+t3.z)/2 };
  const distTip = dist(t4, i4);
  const distShaft = Math.min(dist(i4, t2), dist(i4, t3), dist(i4, mid));
  return {
    distTip, distShaft,
    wrap: distShaft + 0.001 < distTip * 0.55,
    dx: t4.x - i4.x, dy: t4.y - i4.y, dz: t4.z - i4.z,
    thumbUp: tdy / tlen,
    thumbHoriz: Math.sqrt(tdx*tdx + tdz*tdz) / tlen
  };
}
"""


def pose(i_curl, t_curl=0.0, z=30, extra=None, i_spread=None, aside=0.0):
    extra_data = {T1: {"z": z}}
    if extra:
        for name, rots in extra.items():
            if name == T1:
                merged = {"z": z}
                merged.update(rots)
                extra_data[T1] = merged
            else:
                extra_data[name] = rots
    data = {
        "thumb": {"curl": t_curl, "aside": aside} if aside else {"curl": t_curl},
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
    "00_actual_i90": pose(0.90),
    "01_i48": pose(0.48),
    "02_i52": pose(0.52),
    "03_i55": pose(0.55),
    "04_i58": pose(0.58),
    "05_t12_i52": pose(0.52, t_curl=0.12),
    "06_t20_i52": pose(0.52, t_curl=0.20),
    "07_t28_i52": pose(0.52, t_curl=0.28),
    "08_t20_i48": pose(0.48, t_curl=0.20),
    "09_i52_s8": pose(0.52, i_spread=8),
    "10_i52_s-8": pose(0.52, i_spread=-8),
    "11_i52_i2x12": pose(0.52, extra={I2: {"x": 12}}),
    "12_i52_i2x-12": pose(0.52, extra={I2: {"x": -12}}),
    "13_i52_t3z18": pose(0.52, extra={T3: {"z": 18}}),
    "14_i52_t3z-18": pose(0.52, extra={T3: {"z": -18}}),
    "15_i52_t2x-12": pose(0.52, extra={T2: {"x": -12}}),
    "16_t20_i52_t3z16": pose(0.52, t_curl=0.20, extra={T3: {"z": 16}}),
    "17_t18_i50_s6": pose(0.50, t_curl=0.18, i_spread=6),
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

        def cam(orbit):
            page.evaluate(
                """(orbit) => {
                    const mv = document.getElementById('handViewer');
                    mv.cameraTarget = '-0.30m 2.36m 0.20m';
                    mv.cameraOrbit = orbit;
                    mv.fieldOfView = '16deg';
                    mv.jumpCameraToGoal();
                }""",
                orbit,
            )
            time.sleep(0.14)

        ranked = []
        for name, data in CASES.items():
            page.evaluate(
                "(pose) => window.__LSM_CONTROLLER__.applyTestPose(pose)", data
            )
            time.sleep(0.2)
            m = page.evaluate(MEASURE_JS)
            ranked.append((name, m))
            wrap = "WRAP" if m["wrap"] else "ok"
            print(
                f"{name}: tip={m['distTip']:.4f} shaft={m['distShaft']:.4f} {wrap} "
                f"up={m['thumbUp']:.3f} dx={m['dx']:+.3f} dy={m['dy']:+.3f} dz={m['dz']:+.3f}"
            )
            cam("8deg 78deg 0.48m")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_hand.png"))
            cam("12deg 76deg 0.40m")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_tips.png"))

        print("best tip-to-tip without wrap:")
        scored = sorted(
            ranked,
            key=lambda x: (
                1 if x[1]["wrap"] else 0,
                abs(x[1]["dz"]) * 0.4 + x[1]["distTip"],
            ),
        )
        for name, m in scored[:10]:
            wrap = "WRAP" if m["wrap"] else "ok"
            print(
                f"  {name}: tip={m['distTip']:.4f} shaft={m['distShaft']:.4f} {wrap} "
                f"up={m['thumbUp']:.3f} dz={m['dz']:+.3f}"
            )
        browser.close()


if __name__ == "__main__":
    main()
