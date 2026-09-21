"""Tercera pasada de la C: unir los cuatro dedos en un solo arco.

Las capturas anteriores mostraban una garra: los dedos se abrian en abanico.
Aqui se barren patrones de `spread` midiendo la distancia entre puntas vecinas,
ademas de la abertura de la C y la orientacion de la palma.
"""
import itertools
import json
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "fix_c3"
OUT.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=cfix3"

ARM = "mixamorig1RightArm_033"
T1 = "mixamorig1RightHandThumb1_036"
T2 = "mixamorig1RightHandThumb2_037"
T3 = "mixamorig1RightHandThumb3_038"
I1 = "mixamorig1RightHandIndex1_040"
I2 = "mixamorig1RightHandIndex2_041"
M1 = "mixamorig1RightHandMiddle1_044"
M2 = "mixamorig1RightHandMiddle2_045"
R1 = "mixamorig1RightHandRing1_048"
R2 = "mixamorig1RightHandRing2_049"
P1 = "mixamorig1RightHandPinky1_052"
P2 = "mixamorig1RightHandPinky2_053"

MEASURE_JS = """() => {
  const mv = document.getElementById('handViewer');
  function getScene(m) {
    if (m.model && typeof m.model.traverse === 'function') return m.model;
    if (m.model && m.model.scene && typeof m.model.scene.traverse === 'function') return m.model.scene;
    const syms = Object.getOwnPropertySymbols(m);
    for (let i = 0; i < syms.length; i++) {
      const v = m[syms[i]];
      if (v && typeof v === 'object' && typeof v.traverse === 'function') return v;
      if (v && v.model && typeof v.model.traverse === 'function') return v.model;
      if (v && v.target && typeof v.target.traverse === 'function') return v.target;
    }
    return null;
  }
  const scene = getScene(mv);
  if (!scene) return { error: 'no-scene' };
  if (scene.updateMatrixWorld) scene.updateMatrixWorld(true);
  const bones = {};
  scene.traverse((o) => { if (o && o.name) bones[o.name] = o; });
  const names = {
    wrist: 'mixamorig1RightHand_035',
    i1: 'mixamorig1RightHandIndex1_040',
    i4: 'mixamorig1RightHandIndex4_043',
    m1: 'mixamorig1RightHandMiddle1_044',
    m4: 'mixamorig1RightHandMiddle4_047',
    r4: 'mixamorig1RightHandRing4_051',
    p1: 'mixamorig1RightHandPinky1_052',
    p4: 'mixamorig1RightHandPinky4_055',
    t1: 'mixamorig1RightHandThumb1_036',
    t4: 'mixamorig1RightHandThumb4_039',
  };
  const out = {};
  Object.keys(names).forEach((k) => {
    const b = bones[names[k]];
    if (!b || !b.matrixWorld) { out[k] = null; return; }
    const e = b.matrixWorld.elements;
    out[k] = { x: e[12], y: e[13], z: e[14] };
  });
  return out;
}"""


def sub(a, b):
    return (a["x"] - b["x"], a["y"] - b["y"], a["z"] - b["z"])


def nrm(v):
    return (v[0] ** 2 + v[1] ** 2 + v[2] ** 2) ** 0.5


def unit(v):
    n = nrm(v) or 1e-9
    return (v[0] / n, v[1] / n, v[2] / n)


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def d3(a, b):
    return nrm(sub(a, b))


def d2(a, b):
    return ((a["x"] - b["x"]) ** 2 + (a["y"] - b["y"]) ** 2) ** 0.5


SPREADS = {
    "cero": (0, 0, 0, 0),
    "actual": (-4, 3, 4, 6),
    "inv": (4, -3, -4, -6),
    "conv": (8, 3, -3, -8),
    "conv_inv": (-8, -3, 3, 8),
    "suave": (5, 2, -2, -5),
    "suave_inv": (-5, -2, 2, 5),
}

THUMBS = {
    "arc": {T1: {"y": 34, "z": 6}, T2: {"x": -14}, T3: {"x": -8}},
    "wide_lo": {T1: {"y": 40, "z": 14}, T2: {"x": -12}},
    "straight": {T1: {"y": 34, "z": 8}},
}


def build(curl, knuckle, mid, tcurl, taside, tname, sname, wz):
    sp = SPREADS[sname]
    extra = {
        I1: {"x": knuckle},
        M1: {"x": knuckle},
        R1: {"x": knuckle},
        P1: {"x": knuckle},
        ARM: {"z": -18},
    }
    if mid:
        extra[I2] = {"x": mid}
        extra[M2] = {"x": mid}
        extra[R2] = {"x": mid}
        extra[P2] = {"x": mid}
    for bone, rot in THUMBS[tname].items():
        extra[bone] = dict(rot)
    muneca = {"y": 90}
    if wz:
        muneca["z"] = wz
    return {
        "thumb": {"curl": tcurl, "aside": taside},
        "index": {"curl": curl, "spread": sp[0]},
        "middle": {"curl": curl, "spread": sp[1]},
        "ring": {"curl": curl, "spread": sp[2]},
        "pinky": {"curl": curl, "spread": sp[3]},
        "muneca": muneca,
        "extra": extra,
    }


FLAT = {
    "thumb": {"curl": 0.0}, "index": {"curl": 0.0}, "middle": {"curl": 0.0},
    "ring": {"curl": 0.0}, "pinky": {"curl": 0.0},
    "muneca": {}, "extra": {ARM: {"z": -18}},
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
        time.sleep(8)
        ready = False
        for _ in range(80):
            if page.evaluate(
                "() => window.__LSM_CONTROLLER__ && window.__LSM_CONTROLLER__.isModelReady()"
            ):
                ready = True
                break
            time.sleep(0.3)
        if not ready:
            raise RuntimeError("El modelo 3D no cargo a tiempo")
        time.sleep(1.0)

        def measure(pose):
            page.evaluate("(p) => window.__LSM_CONTROLLER__.applyTestPose(p)", pose)
            time.sleep(0.09)
            return page.evaluate(MEASURE_JS)

        flat_m = measure(FLAT)
        FL = d3(flat_m["i1"], flat_m["i4"])

        def metrics(m):
            n = unit(cross(sub(m["i1"], m["wrist"]), sub(m["p1"], m["wrist"])))
            juntos = (
                d3(m["i4"], m["m4"]) + d3(m["m4"], m["r4"]) + d3(m["r4"], m["p4"])
            ) / FL
            return {
                "ap": d2(m["i4"], m["t4"]) / FL,
                "chord": d3(m["i1"], m["i4"]) / FL,
                "juntos": juntos,
                "nz": abs(n[2]),
                "dy": (m["i4"]["y"] - m["t4"]["y"]) / FL,
                "open_x": ((m["i4"]["x"] + m["t4"]["x"]) / 2 - m["wrist"]["x"]) / FL,
            }

        base = metrics(flat_m)
        print(f"largo de dedo {FL:.4f} | mano plana juntos={base['juntos']:.2f}", flush=True)

        rows = []
        for curl, knuckle, mid, tcurl, taside, tname, sname, wz in itertools.product(
            (0.24, 0.30),
            (22, 28, 34),
            (14, 20),
            (0.18, 0.28),
            (0.45,),
            tuple(THUMBS),
            tuple(SPREADS),
            (0, -15, -30),
        ):
            pose = build(curl, knuckle, mid, tcurl, taside, tname, sname, wz)
            met = metrics(measure(pose))
            met.update({
                "curl": curl, "knuckle": knuckle, "mid": mid, "tcurl": tcurl,
                "taside": taside, "thumb": tname, "spread": sname, "wz": wz,
            })
            rows.append(met)

        ok = [r for r in rows if 0.28 <= r["ap"] <= 0.44 and r["dy"] > 0.10]
        for r in ok:
            r["score"] = (
                abs(r["ap"] - 0.36) * 3.0
                + abs(r["chord"] - 0.82) * 2.0
                + r["juntos"] * 1.8
                + r["nz"] * 1.0
            )
        ok.sort(key=lambda r: r["score"])
        print(f"probados {len(rows)}, validos {len(ok)}", flush=True)
        for r in ok[:18]:
            print(
                f"{r['score']:.3f} ap={r['ap']:.2f} cuerda={r['chord']:.2f} "
                f"juntos={r['juntos']:.2f} dy={r['dy']:+.2f} nz={r['nz']:.2f} | "
                f"curl={r['curl']} nud={r['knuckle']} med={r['mid']} tc={r['tcurl']} "
                f"pulgar={r['thumb']} sep={r['spread']} wz={r['wz']}",
                flush=True,
            )

        viewer = page.query_selector("#viewer")

        def cam(target, orbit, fov):
            page.evaluate(
                """(a) => {
                    const mv = document.getElementById('handViewer');
                    if (!mv) return;
                    mv.cameraTarget = a.target;
                    mv.cameraOrbit = a.orbit;
                    mv.fieldOfView = a.fov;
                    if (typeof mv.jumpCameraToGoal === 'function') mv.jumpCameraToGoal();
                }""",
                {"target": target, "orbit": orbit, "fov": fov},
            )
            time.sleep(0.25)

        chosen, seen = [], set()
        for r in ok:
            key = (r["spread"], r["thumb"], r["curl"])
            if key in seen:
                continue
            seen.add(key)
            chosen.append(r)
            if len(chosen) == 6:
                break

        for i, r in enumerate(chosen):
            pose = build(
                r["curl"], r["knuckle"], r["mid"], r["tcurl"], r["taside"],
                r["thumb"], r["spread"], r["wz"],
            )
            page.evaluate("(p) => window.__LSM_CONTROLLER__.applyTestPose(p)", pose)
            time.sleep(0.3)
            tag = f"{i}_{r['spread']}_{r['thumb']}_c{r['curl']}_wz{r['wz']}"
            cam("0m 2.45m 0.15m", "0deg 84deg 2.5m", "30deg")
            viewer.screenshot(path=str(OUT / f"{tag}_front.png"))
            cam("-0.30m 2.36m 0.20m", "0deg 82deg 0.52m", "18deg")
            viewer.screenshot(path=str(OUT / f"{tag}_mano.png"))
            print(f"captura {tag}", flush=True)

        (OUT / "result.json").write_text(
            json.dumps({"finger_len": FL, "top": ok[:20], "chosen": chosen}, indent=2),
            encoding="utf-8",
        )
        browser.close()


if __name__ == "__main__":
    sys.exit(main())
