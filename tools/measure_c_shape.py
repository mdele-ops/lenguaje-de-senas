"""Mide la forma de la C: abertura pulgar-indice, curvatura y orientacion del arco.

Barre candidatos y ordena por parecido a la foto de referencia:
  - abertura clara entre puntas (no una O / pinza)
  - cuatro dedos juntos y curvados en un solo arco
  - pulgar abajo, dedos arriba, arco de perfil (visible desde la camara frontal)
"""
import itertools
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "measure_c"
OUT.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=cmeasure1"

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
  function pos(name) {
    const b = bones[name];
    if (!b || !b.matrixWorld) return null;
    const e = b.matrixWorld.elements;
    return { x: e[12], y: e[13], z: e[14] };
  }
  const names = {
    wrist: 'mixamorig1RightHand_035',
    i1: 'mixamorig1RightHandIndex1_040',
    i4: 'mixamorig1RightHandIndex4_043',
    m4: 'mixamorig1RightHandMiddle4_047',
    p4: 'mixamorig1RightHandPinky4_055',
    t1: 'mixamorig1RightHandThumb1_036',
    t4: 'mixamorig1RightHandThumb4_039',
  };
  const out = {};
  Object.keys(names).forEach((k) => { out[k] = pos(names[k]); });
  return out;
}"""


def sub(a, b):
    return (a["x"] - b["x"], a["y"] - b["y"], a["z"] - b["z"])


def norm(v):
    return (v[0] ** 2 + v[1] ** 2 + v[2] ** 2) ** 0.5


def cross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def dist(a, b):
    return norm(sub(a, b))


def fingers(curl, tcurl, taside):
    return {
        "thumb": {"curl": tcurl, "aside": taside},
        "index": {"curl": curl, "spread": -4},
        "middle": {"curl": curl, "spread": 3},
        "ring": {"curl": curl, "spread": 4},
        "pinky": {"curl": curl, "spread": 6},
    }


def build(curl, knuckle, mid, tcurl, taside, thumb_extra, muneca):
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
    for bone, rot in thumb_extra.items():
        extra[bone] = dict(rot)
    pose = fingers(curl, tcurl, taside)
    pose["muneca"] = dict(muneca)
    pose["extra"] = extra
    return pose


FLAT = {
    "thumb": {"curl": 0.0},
    "index": {"curl": 0.0},
    "middle": {"curl": 0.0},
    "ring": {"curl": 0.0},
    "pinky": {"curl": 0.0},
    "muneca": {"y": 50, "z": 45},
    "extra": {ARM: {"z": -18}},
}

CURRENT = build(
    0.28, 36, 8, 0.26, 0.42,
    {T1: {"y": 8, "z": 30}, T2: {"x": -16}, T3: {"x": -6}},
    {"y": 50, "z": 45},
)

MUNECA = {"y": 50, "z": 45}

THUMB_OPTS = {
    "t_low": {T1: {"y": 0, "z": 10}},
    "t_low2": {T1: {"y": -10, "z": 18}},
    "t_mid": {T1: {"y": 14, "z": 12}},
    "t_out": {T1: {"y": 30, "z": 0}},
    "t_out2": {T1: {"y": 44, "z": -6}},
    "t_rail": {T1: {"y": 8, "z": 24}, T2: {"x": -8}},
    "t_flat": {T1: {"y": 20, "z": 6}, T2: {"x": 6}},
}


def main():
    combos = []
    for curl, knuckle, mid, tcurl, taside, tname in itertools.product(
        (0.0, 0.08, 0.16, 0.24),
        (18, 28, 38, 48),
        (0, 12),
        (0.0, 0.12, 0.26),
        (0.2, 0.5, 0.8),
        tuple(THUMB_OPTS),
    ):
        combos.append(
            (
                f"c{curl}_k{knuckle}_m{mid}_tc{tcurl}_ta{taside}_{tname}",
                build(curl, knuckle, mid, tcurl, taside, THUMB_OPTS[tname], MUNECA),
            )
        )

    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="chrome",
            args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"],
        )
        page = browser.new_page(viewport={"width": 900, "height": 800})
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
            time.sleep(0.12)
            return page.evaluate(MEASURE_JS)

        flat = measure(FLAT)
        finger_len = dist(flat["i1"], flat["i4"])
        thumb_len = dist(flat["t1"], flat["t4"])
        print(f"referencia: dedo={finger_len:.4f} pulgar={thumb_len:.4f}")

        def metrics(m):
            ap = dist(m["t4"], m["i4"]) / finger_len
            chord = dist(m["i1"], m["i4"]) / finger_len
            juntos = dist(m["i4"], m["p4"]) / finger_len
            n = cross(sub(m["i4"], m["wrist"]), sub(m["t4"], m["wrist"]))
            ln = norm(n) or 1e-9
            plano = abs(n[0]) / ln
            dy = (m["i4"]["y"] - m["t4"]["y"]) / finger_len
            return {
                "ap": ap,
                "chord": chord,
                "juntos": juntos,
                "plano": plano,
                "dy": dy,
            }

        cur = metrics(measure(CURRENT))
        print("C actual:", {k: round(v, 3) for k, v in cur.items()})

        # Objetivos leidos de la foto: abertura clara (~un pulgar de hueco),
        # dedos curvados ~120 grados (cuerda ~0.82), puntas juntas, arco de perfil.
        TARGET_AP = 0.62
        TARGET_CHORD = 0.82

        rows = []
        for name, pose in combos:
            m = measure(pose)
            if not m or m.get("error"):
                continue
            met = metrics(m)
            score = (
                abs(met["ap"] - TARGET_AP) * 2.2
                + abs(met["chord"] - TARGET_CHORD) * 1.8
                + met["juntos"] * 0.9
                + (1 - met["plano"]) * 1.2
                + max(0.0, -met["dy"]) * 1.5
            )
            met["score"] = score
            met["name"] = name
            rows.append(met)

        rows.sort(key=lambda r: r["score"])
        print(f"\n=== MEJORES {len(rows)} candidatos ===")
        for r in rows[:20]:
            print(
                f"{r['score']:.3f}  ap={r['ap']:.2f} cuerda={r['chord']:.2f} "
                f"juntos={r['juntos']:.2f} plano={r['plano']:.2f} dy={r['dy']:+.2f}  {r['name']}"
            )

        (OUT / "ranking.json").write_text(
            json.dumps({"actual": cur, "top": rows[:40]}, indent=2), encoding="utf-8"
        )
        browser.close()


if __name__ == "__main__":
    main()
