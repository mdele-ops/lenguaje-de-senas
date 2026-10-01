"""F: pulgar a 90 grados; indice cruza a la mitad formando una cruz."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_f6"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=f6"

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
  function sub(a, b) { return { x: a.x-b.x, y: a.y-b.y, z: a.z-b.z }; }
  function len(v) { return Math.sqrt(v.x*v.x+v.y*v.y+v.z*v.z) || 1; }
  function mid(a, b) { return { x:(a.x+b.x)/2, y:(a.y+b.y)/2, z:(a.z+b.z)/2 }; }
  const t1 = pos('mixamorig1RightHandThumb1_036');
  const t2 = pos('mixamorig1RightHandThumb2_037');
  const t3 = pos('mixamorig1RightHandThumb3_038');
  const t4 = pos('mixamorig1RightHandThumb4_039');
  const i1 = pos('mixamorig1RightHandIndex1_040');
  const i2 = pos('mixamorig1RightHandIndex2_041');
  const i4 = pos('mixamorig1RightHandIndex4_043');
  if (!t1 || !t4 || !i1 || !i4) return { error: 'bones' };
  const td = sub(t4, t1);
  const id = sub(i4, i1);
  const tl = len(td), il = len(id);
  const dot = (td.x*id.x + td.y*id.y + td.z*id.z) / (tl*il);
  const angle = Math.acos(Math.max(-1, Math.min(1, dot))) * 180 / Math.PI;
  const tMid = mid(t2, t3);
  const iMid = mid(i1, i2);
  const dx = iMid.x-tMid.x, dy = iMid.y-tMid.y, dz = iMid.z-tMid.z;
  return {
    angle,
    thumbHoriz: 1 - Math.abs(td.y / tl),
    indexUp: id.y / il,
    dist: Math.sqrt(dx*dx+dy*dy+dz*dz),
    dx, dy, dz,
    tdy: td.y / tl
  };
}
"""


def pose(thumb, index, extra=None):
    data = {
        "thumb": thumb,
        "index": index if isinstance(index, dict) else {"curl": index},
        "middle": {"curl": 0.0, "spread": -2},
        "ring": {"curl": 0.0, "spread": -3},
        "pinky": {"curl": 0.0, "spread": -5},
    }
    if extra:
        data["extra"] = extra
    return data


CASES = {
    "00_actual": pose(
        {"curl": 0.74, "aside": -0.5},
        0.82,
        {T1: {"y": -65}},
    ),
    "01_L_up": pose({"curl": 0.05, "aside": 0.55}, 0.0),
    "02_L_aside80": pose({"curl": 0.0, "aside": 0.8}, 0.0),
    "03_L_aside100": pose({"curl": 0.0, "aside": 1.0}, 0.0),
    "04_y90": pose({"curl": 0.05, "aside": 0.2}, 0.0, {T1: {"y": 90}}),
    "05_y-90": pose({"curl": 0.05, "aside": 0.2}, 0.0, {T1: {"y": -90}}),
    "06_z90": pose({"curl": 0.05, "aside": 0.2}, 0.0, {T1: {"z": 90}}),
    "07_z-90": pose({"curl": 0.05, "aside": 0.2}, 0.0, {T1: {"z": -90}}),
    "08_x90": pose({"curl": 0.05, "aside": 0.2}, 0.0, {T1: {"x": 90}}),
    "09_x-90": pose({"curl": 0.05, "aside": 0.2}, 0.0, {T1: {"x": -90}}),
    "10_L_y40": pose({"curl": 0.05, "aside": 0.55}, 0.0, {T1: {"y": 40}}),
    "11_L_y-40": pose({"curl": 0.05, "aside": 0.55}, 0.0, {T1: {"y": -40}}),
    "12_L_z40": pose({"curl": 0.05, "aside": 0.55}, 0.0, {T1: {"z": 40}}),
    "13_L_z-40": pose({"curl": 0.05, "aside": 0.55}, 0.0, {T1: {"z": -40}}),
    "14_cross_y-70": pose({"curl": 0.1, "aside": 0.7}, 0.15, {T1: {"y": -70}}),
    "15_cross_z60": pose({"curl": 0.0, "aside": 0.6}, 0.10, {T1: {"z": 60, "y": -20}}),
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
                f"idxUp={m['indexUp']:.3f} dist={m['dist']:.4f}"
            )
            cam("-0.30m 2.36m 0.20m", "8deg 78deg 0.50m", "18deg")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_hand.png"))
            cam("-0.30m 2.36m 0.20m", "-40deg 80deg 0.55m", "20deg")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_palm.png"))

        print("closest to 90 + horizontal thumb:")
        scored = sorted(
            ranked,
            key=lambda x: abs(x[1]["angle"] - 90) * 0.01
            + (1 - x[1]["thumbHoriz"])
            + x[1]["dist"] * 2,
        )
        for name, m in scored[:8]:
            print(
                f"  {name}: ang={m['angle']:.1f} horiz={m['thumbHoriz']:.3f} dist={m['dist']:.4f}"
            )
        browser.close()


if __name__ == "__main__":
    main()
