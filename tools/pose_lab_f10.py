"""Mueve el pulgar horizontal (z90) hacia el centro del indice."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_f10"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=f10"

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
  const i2 = pos('mixamorig1RightHandIndex2_041');
  const i4 = pos('mixamorig1RightHandIndex4_043');
  if (!t1||!t4||!i1||!i4) return {error:'bones'};
  const td = sub(t4,t1), id = sub(i4,i1);
  const tl = len(td), il = len(id);
  const dot = (td.x*id.x+td.y*id.y+td.z*id.z)/(tl*il);
  const angle = Math.acos(Math.max(-1,Math.min(1,dot)))*180/Math.PI;
  const tMid = {x:(t2.x+t3.x)/2,y:(t2.y+t3.y)/2,z:(t2.z+t3.z)/2};
  const iMid = {x:(i1.x+i2.x)/2,y:(i1.y+i2.y)/2,z:(i1.z+i2.z)/2};
  const dx=tMid.x-iMid.x, dy=tMid.y-iMid.y, dz=tMid.z-iMid.z;
  return {
    angle,
    thumbHoriz: 1-Math.abs(td.y/tl),
    indexUp: id.y/il,
    dist: Math.sqrt(dx*dx+dy*dy+dz*dz),
    dx, dy, dz
  };
}
"""


def pose(t1y=0, t1x=0, aside=0.2, t2x=0, t_curl=0.05, t1z=90):
    extra = {T1: {"z": t1z}}
    if t1y:
        extra[T1]["y"] = t1y
    if t1x:
        extra[T1]["x"] = t1x
    if t2x:
        extra[T2] = {"x": t2x}
    return {
        "thumb": {"curl": t_curl, "aside": aside},
        "index": {"curl": 0.0},
        "middle": {"curl": 0.0, "spread": -2},
        "ring": {"curl": 0.0, "spread": -3},
        "pinky": {"curl": 0.0, "spread": -5},
        "extra": extra,
    }


CASES = {
    "00": pose(),
    "01_y-20": pose(t1y=-20),
    "02_y20": pose(t1y=20),
    "03_y40": pose(t1y=40),
    "04_y-40": pose(t1y=-40),
    "05_x20": pose(t1x=20),
    "06_x-20": pose(t1x=-20),
    "07_x40": pose(t1x=40),
    "08_x-40": pose(t1x=-40),
    "09_as-2": pose(aside=-0.2),
    "10_as06": pose(aside=0.6),
    "11_t2x25": pose(t2x=25),
    "12_t2x-25": pose(t2x=-25),
    "13_y30_x-20": pose(t1y=30, t1x=-20),
    "14_y30_as06": pose(t1y=30, aside=0.6),
    "15_y40_x-30": pose(t1y=40, t1x=-30),
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
            time.sleep(0.14)

        ranked = []
        for name, data in CASES.items():
            page.evaluate(
                "(pose) => window.__LSM_CONTROLLER__.applyTestPose(pose)", data
            )
            time.sleep(0.18)
            m = page.evaluate(MEASURE_JS)
            ranked.append((name, m))
            print(
                f"{name}: ang={m['angle']:.1f} horiz={m['thumbHoriz']:.3f} "
                f"dist={m['dist']:.4f} dx={m['dx']:+.3f} dy={m['dy']:+.3f} dz={m['dz']:+.3f}"
            )
            cam("-0.30m 2.36m 0.20m", "8deg 78deg 0.50m", "18deg")
            viewer.screenshot(path=str(OUT_DIR / f"{name}_hand.png"))

        print("closest:")
        for name, m in sorted(ranked, key=lambda x: x[1]["dist"])[:8]:
            print(
                f"  {name}: dist={m['dist']:.4f} ang={m['angle']:.1f} "
                f"horiz={m['thumbHoriz']:.3f} dx={m['dx']:+.3f} dy={m['dy']:+.3f}"
            )
        browser.close()


if __name__ == "__main__":
    main()
