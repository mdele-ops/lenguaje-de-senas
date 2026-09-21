"""F: pulgar horizontal a 90; indice cruza al centro."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_f7"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=f7"

T1 = "mixamorig1RightHandThumb1_036"
T2 = "mixamorig1RightHandThumb2_037"

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
  function sub(a,b){return {x:a.x-b.x,y:a.y-b.y,z:a.z-b.z};}
  function len(v){return Math.sqrt(v.x*v.x+v.y*v.y+v.z*v.z)||1;}
  const t1 = pos('mixamorig1RightHandThumb1_036');
  const t2 = pos('mixamorig1RightHandThumb2_037');
  const t3 = pos('mixamorig1RightHandThumb3_038');
  const t4 = pos('mixamorig1RightHandThumb4_039');
  const i1 = pos('mixamorig1RightHandIndex1_040');
  const i4 = pos('mixamorig1RightHandIndex4_043');
  if (!t1||!t4||!i1||!i4) return {error:'bones'};
  const td = sub(t4,t1), id = sub(i4,i1);
  const tl = len(td), il = len(id);
  const dot = (td.x*id.x+td.y*id.y+td.z*id.z)/(tl*il);
  const angle = Math.acos(Math.max(-1,Math.min(1,dot)))*180/Math.PI;
  const mid = {x:(t2.x+t3.x)/2,y:(t2.y+t3.y)/2,z:(t2.z+t3.z)/2};
  const dx=i4.x-mid.x, dy=i4.y-mid.y, dz=i4.z-mid.z;
  return {
    angle,
    thumbHoriz: 1-Math.abs(td.y/tl),
    indexUp: id.y/il,
    dist: Math.sqrt(dx*dx+dy*dy+dz*dz),
    dx, dy, dz
  };
}
"""


def pose(thumb, index, extra=None):
    data = {
        "thumb": thumb,
        "index": {"curl": index} if not isinstance(index, dict) else index,
        "middle": {"curl": 0.0, "spread": -2},
        "ring": {"curl": 0.0, "spread": -3},
        "pinky": {"curl": 0.0, "spread": -5},
    }
    if extra:
        data["extra"] = extra
    return data


CASES = {
    "00_z90": pose({"curl": 0.05, "aside": 0.2}, 0.0, {T1: {"z": 90}}),
    "01_z90_i40": pose({"curl": 0.05, "aside": 0.2}, 0.40, {T1: {"z": 90}}),
    "02_z90_i55": pose({"curl": 0.05, "aside": 0.2}, 0.55, {T1: {"z": 90}}),
    "03_z90_i70": pose({"curl": 0.05, "aside": 0.2}, 0.70, {T1: {"z": 90}}),
    "04_z75_i55": pose({"curl": 0.05, "aside": 0.25}, 0.55, {T1: {"z": 75}}),
    "05_z105_i55": pose({"curl": 0.05, "aside": 0.15}, 0.55, {T1: {"z": 105}}),
    "06_z90_y-30_i50": pose({"curl": 0.08, "aside": 0.3}, 0.50, {T1: {"z": 90, "y": -30}}),
    "07_z90_y30_i50": pose({"curl": 0.08, "aside": 0.3}, 0.50, {T1: {"z": 90, "y": 30}}),
    "08_z-40_i50": pose({"curl": 0.05, "aside": 0.55}, 0.50, {T1: {"z": -40}}),
    "09_z-50_i60": pose({"curl": 0.05, "aside": 0.6}, 0.60, {T1: {"z": -50}}),
    "10_z80_as-3_i55": pose({"curl": 0.1, "aside": -0.3}, 0.55, {T1: {"z": 80}}),
    "11_b_z90": pose({"curl": 0.4, "aside": -0.4}, 0.50, {T1: {"z": 90, "y": -20}}),
    "12_z90_t2x20_i55": pose(
        {"curl": 0.05, "aside": 0.2},
        0.55,
        {T1: {"z": 90}, T2: {"x": 20}},
    ),
    "13_z90_t2x-20_i55": pose(
        {"curl": 0.05, "aside": 0.2},
        0.55,
        {T1: {"z": 90}, T2: {"x": -20}},
    ),
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

        def cam(target, orbit, fov):
            page.evaluate(
                """(a) => {
                    const mv = document.getElementById('handViewer');
                    mv.cameraTarget = a.target;
                    mv.cameraOrbit = a.orbit;
                    mv.fieldOfView = a.fov;
                    mv.jumpCameraToGoal();
                }""",
                {"target": target, "orbit": orbit, "fov": fov},
            )
            time.sleep(0.16)

        ranked = []
        for name, data in CASES.items():
            page.evaluate(
                "(pose) => window.__LSM_CONTROLLER__.applyTestPose(pose)", data
            )
            time.sleep(0.2)
            m = page.evaluate(MEASURE_JS)
            ranked.append((name, m))
            print(
                f"{name}: ang={m['angle']:.1f} horiz={m['thumbHoriz']:.3f} "
                f"idxUp={m['indexUp']:.3f} dist={m['dist']:.4f} "
                f"dx={m['dx']:+.3f} dy={m['dy']:+.3f} dz={m['dz']:+.3f}"
            )
            cam("-0.30m 2.36m 0.20m", "8deg 78deg 0.50m", "18deg")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_hand.png"))
            cam("-0.30m 2.36m 0.20m", "-40deg 80deg 0.55m", "20deg")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_palm.png"))

        print("best cross (90deg + horiz + close):")
        scored = sorted(
            ranked,
            key=lambda x: abs(x[1]["angle"] - 90) * 0.008
            + (1 - x[1]["thumbHoriz"]) * 0.6
            + x[1]["dist"] * 4,
        )
        for name, m in scored[:8]:
            print(
                f"  {name}: ang={m['angle']:.1f} horiz={m['thumbHoriz']:.3f} dist={m['dist']:.4f}"
            )
        browser.close()


if __name__ == "__main__":
    main()
