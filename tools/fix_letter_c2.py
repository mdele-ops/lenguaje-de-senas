"""Corrige la C usando la normal de la palma y calibrando con letras ya validadas.

Etapa 0: mide B (palma al frente) y O (puntas juntas) para saber que valores
         numericos corresponden a cada forma real.
Etapa 1: gira la muneca hasta que la palma quede de lado (normal perpendicular
         al eje de la camara), con la mano en alto. Asi el arco de los dedos
         cae en el plano de la pantalla y la C se lee.
Etapa 2: ajusta curvatura y pulgar; se descartan las manos casi planas y las
         que cierran como O. Al final captura la mano con la camara centrada
         en la muneca medida.
"""
import itertools
import json
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "fix_c2"
OUT.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=cfix2"

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
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def d3(a, b):
    return nrm(sub(a, b))


def d2(a, b):
    return ((a["x"] - b["x"]) ** 2 + (a["y"] - b["y"]) ** 2) ** 0.5


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
    for bone, rot in (thumb_extra or {}).items():
        extra[bone] = dict(rot)
    return {
        "thumb": {"curl": tcurl, "aside": taside},
        "index": {"curl": curl, "spread": -4},
        "middle": {"curl": curl, "spread": 3},
        "ring": {"curl": curl, "spread": 4},
        "pinky": {"curl": curl, "spread": 6},
        "muneca": dict(muneca),
        "extra": extra,
    }


FLAT = {
    "thumb": {"curl": 0.0},
    "index": {"curl": 0.0},
    "middle": {"curl": 0.0},
    "ring": {"curl": 0.0},
    "pinky": {"curl": 0.0},
    "muneca": {},
    "extra": {ARM: {"z": -18}},
}

PROBE = dict(curl=0.30, knuckle=34, mid=12, tcurl=0.12, taside=0.5,
             thumb_extra={T1: {"y": 34, "z": 6}, T2: {"x": -14}, T3: {"x": -8}})

THUMB_OPTS = {
    "arc": {T1: {"y": 34, "z": 6}, T2: {"x": -14}, T3: {"x": -8}},
    "arc_lo": {T1: {"y": 26, "z": 16}, T2: {"x": -16}, T3: {"x": -8}},
    "wide": {T1: {"y": 46, "z": 2}, T2: {"x": -10}},
    "wide_lo": {T1: {"y": 40, "z": 14}, T2: {"x": -12}},
    "straight": {T1: {"y": 34, "z": 8}},
    "up": {T1: {"y": 20, "z": -8}, T2: {"x": -12}},
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

        flat = measure(FLAT)
        FL = d3(flat["i1"], flat["i4"])

        def metrics(m):
            # normal de la palma: no depende de cuanto se curven los dedos
            n = unit(cross(sub(m["i1"], m["wrist"]), sub(m["p1"], m["wrist"])))
            up = unit(sub(m["m1"], m["wrist"]))
            return {
                "ap": d2(m["i4"], m["t4"]) / FL,
                "ap3d": d3(m["i4"], m["t4"]) / FL,
                "chord": d3(m["i1"], m["i4"]) / FL,
                "nz": abs(n[2]),
                "nx": abs(n[0]),
                "up": up[1],
                "dy": (m["i4"]["y"] - m["t4"]["y"]) / FL,
                "open_x": ((m["i4"]["x"] + m["t4"]["x"]) / 2 - m["wrist"]["x"]) / FL,
            }

        def show(tag, met):
            print(
                f"{tag:14} ap={met['ap']:.2f} ap3d={met['ap3d']:.2f} cuerda={met['chord']:.2f} "
                f"nz={met['nz']:.2f} nx={met['nx']:.2f} arriba={met['up']:+.2f} "
                f"dy={met['dy']:+.2f} abre={met['open_x']:+.2f}",
                flush=True,
            )

        print(f"largo de dedo: {FL:.4f}\n=== ETAPA 0: calibracion ===", flush=True)
        show("mano_plana", metrics(flat))
        for letra in ("B", "O", "C"):
            pose = page.evaluate(
                "(l) => { const s = window.__LSM_CONTROLLER__.getSena(l); return s && s.pose; }",
                letra,
            )
            if pose:
                show(f"letra_{letra}", metrics(measure(pose)))

        # ---------- Etapa 1: palma de lado, mano en alto ----------
        print("\n=== ETAPA 1: orientacion (palma de lado) ===", flush=True)
        wrist_rows = []
        for wx, wy, wz in itertools.product(
            (-40, -20, 0, 20, 40),
            (-90, -60, -30, 0, 30, 60, 90),
            (-30, -15, 0, 15, 30, 45, 60),
        ):
            muneca = {}
            if wx:
                muneca["x"] = wx
            if wy:
                muneca["y"] = wy
            if wz:
                muneca["z"] = wz
            met = metrics(measure(build(muneca=muneca, **PROBE)))
            score = (
                met["nz"] * 3.0
                + max(0.0, 0.55 - met["up"]) * 2.5
                + max(0.0, 0.20 - met["dy"]) * 1.5
                + max(0.0, 0.10 - met["open_x"]) * 1.5
            )
            met.update({"x": wx, "y": wy, "z": wz, "score": score})
            wrist_rows.append(met)

        wrist_rows.sort(key=lambda r: r["score"])
        for r in wrist_rows[:12]:
            print(
                f"{r['score']:.3f}  x={r['x']:+4d} y={r['y']:+4d} z={r['z']:+4d}  "
                f"nz={r['nz']:.2f} arriba={r['up']:+.2f} dy={r['dy']:+.2f} "
                f"abre={r['open_x']:+.2f} ap={r['ap']:.2f}",
                flush=True,
            )

        best = wrist_rows[0]
        wrist = {k: best[k] for k in ("x", "y", "z") if best[k]}
        print(f"muneca elegida: {wrist}", flush=True)

        # ---------- Etapa 2: forma, con curvatura obligatoria ----------
        print("\n=== ETAPA 2: dedos y pulgar ===", flush=True)
        rows = []
        for curl, knuckle, mid, tcurl, taside, tname in itertools.product(
            (0.16, 0.22, 0.28, 0.34, 0.40),
            (26, 34, 42, 50),
            (6, 14, 22),
            (0.08, 0.18, 0.28),
            (0.35, 0.6),
            tuple(THUMB_OPTS),
        ):
            met = metrics(
                measure(
                    build(curl, knuckle, mid, tcurl, taside, THUMB_OPTS[tname], wrist)
                )
            )
            met.update(
                {
                    "curl": curl,
                    "knuckle": knuckle,
                    "mid": mid,
                    "tcurl": tcurl,
                    "taside": taside,
                    "thumb": tname,
                }
            )
            rows.append(met)

        # Filtros duros: dedos realmente curvados y abertura de C (ni O ni mano abierta)
        ok = [
            r for r in rows
            if 0.74 <= r["chord"] <= 0.89 and 0.26 <= r["ap"] <= 0.46 and r["dy"] > 0.05
        ]
        print(f"(probados {len(rows)}, validos {len(ok)})", flush=True)
        for r in ok:
            r["score"] = (
                abs(r["ap"] - 0.36) * 3.0
                + abs(r["chord"] - 0.82) * 2.2
                + r["nz"] * 1.2
                + max(0.0, 0.20 - r["dy"]) * 1.5
            )
        ok.sort(key=lambda r: r["score"])
        for r in ok[:16]:
            print(
                f"{r['score']:.3f}  ap={r['ap']:.2f} cuerda={r['chord']:.2f} nz={r['nz']:.2f} "
                f"dy={r['dy']:+.2f} abre={r['open_x']:+.2f}  curl={r['curl']} "
                f"nudillo={r['knuckle']} medio={r['mid']} tcurl={r['tcurl']} "
                f"taside={r['taside']} pulgar={r['thumb']}",
                flush=True,
            )

        # ---------- Capturas centradas en la mano ----------
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
            key = (r["thumb"], r["curl"], r["knuckle"])
            if key in seen:
                continue
            seen.add(key)
            chosen.append(r)
            if len(chosen) == 6:
                break

        for i, r in enumerate(chosen):
            pose = build(
                r["curl"], r["knuckle"], r["mid"], r["tcurl"], r["taside"],
                THUMB_OPTS[r["thumb"]], wrist,
            )
            m = measure(pose)
            w = m["wrist"]
            tag = f"{i}_{r['thumb']}_c{r['curl']}_k{r['knuckle']}_ap{r['ap']:.2f}"
            cam("0m 2.45m 0.15m", "0deg 84deg 2.5m", "30deg")
            viewer.screenshot(path=str(OUT / f"{tag}_front.png"))
            cam(f"{w['x']:.3f}m {w['y'] + 0.06:.3f}m {w['z']:.3f}m", "0deg 84deg 0.55m", "20deg")
            viewer.screenshot(path=str(OUT / f"{tag}_zoom.png"))
            print(f"captura {tag}", flush=True)

        (OUT / "result.json").write_text(
            json.dumps(
                {"finger_len": FL, "wrist": wrist, "wrist_top": wrist_rows[:10],
                 "shape_top": ok[:20], "chosen": chosen},
                indent=2,
            ),
            encoding="utf-8",
        )
        browser.close()


if __name__ == "__main__":
    sys.exit(main())
