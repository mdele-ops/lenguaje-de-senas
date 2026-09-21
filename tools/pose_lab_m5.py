"""M lab 5: tres lomos sobre el pulgar, menique cerrado, yema asomando.

Parte de 08_fist_in (pulgar delante de la palma, across ~0.8) y reparte
MCP/PIP/DIP a mano: la E enrolla las yemas (DIP alto); la M las deja
apoyadas sobre el pulgar para que se vean tres lomos, no un puno.
"""
import json
import time
from pathlib import Path

from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright

from overlay_e import PROJECT_JS, dibujar_overlay, nombres_huesos
from pose_lab_e import ARM, BONES, FINGERS, HAND_POS_JS, T1, T2, T3, _GET_SCENE, free_camera, set_cam
from pulgar_e import PULGAR_JS
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "lab_m5"
OUT.mkdir(parents=True, exist_ok=True)
REF = ROOT / "tools" / "screenshots" / "referencia" / "M_usuario.png"

import search_e9 as se9

se9.URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=m5"

FAN3 = (-1.2, -0.2, 1.0, 2.2)

MEASURE_JS = (
    """
() => {
  const mv = document.getElementById('handViewer');
"""
    + _GET_SCENE
    + """
  const scene = getScene(mv);
  if (!scene) return { error: 'no-scene' };
  scene.updateMatrixWorld(true);
  const B = {};
  scene.traverse((o) => { if (o && o.name) B[o.name] = o; });
  const P = (n) => {
    const b = B[n];
    if (!b || !b.matrixWorld) return null;
    const e = b.matrixWorld.elements;
    return { x: e[12], y: e[13], z: e[14] };
  };
  const d = (a, b) => Math.hypot(a.x-b.x, a.y-b.y, a.z-b.z);
  const sub = (a, b) => ({ x: a.x-b.x, y: a.y-b.y, z: a.z-b.z });
  const dot = (a, b) => a.x*b.x + a.y*b.y + a.z*b.z;
  const len = (a) => Math.hypot(a.x, a.y, a.z);
  const norm = (a) => { const l = len(a) || 1; return { x: a.x/l, y: a.y/l, z: a.z/l }; };

  const wrist = P('mixamorig1RightHand_035');
  const knuI = P('mixamorig1RightHandIndex1_040');
  const knuP = P('mixamorig1RightHandPinky1_052');
  const t2 = P('mixamorig1RightHandThumb2_037');
  const t4 = P('mixamorig1RightHandThumb4_039');
  const i4 = P('mixamorig1RightHandIndex4_043');
  const m4 = P('mixamorig1RightHandMiddle4_047');
  const r4 = P('mixamorig1RightHandRing4_051');
  const p4 = P('mixamorig1RightHandPinky4_055');
  const palm = d(wrist, knuI) || 1;
  const axis = sub(t4, t2);
  const axisLen = len(axis) || 1;
  function distAxis(p) {
    const w = sub(p, t2);
    const t = Math.max(0, Math.min(1, dot(w, axis) / (axisLen * axisLen)));
    const q = { x: t2.x + t*axis.x, y: t2.y + t*axis.y, z: t2.z + t*axis.z };
    return d(p, q) / palm;
  }
  const gapRP = sub(p4, r4);
  const midRP = { x: (r4.x+p4.x)/2, y: (r4.y+p4.y)/2, z: (r4.z+p4.z)/2 };
  return {
    dI: distAxis(i4), dM: distAxis(m4), dR: distAxis(r4), dP: distAxis(p4),
    togIM: d(i4, m4) / palm,
    togMR: d(m4, r4) / palm,
    togRP: d(r4, p4) / palm,
    peek: d(t4, midRP) / palm,
    pinkyLower: (i4.y - p4.y) / palm,
  };
}
"""
)


def four(v):
    return tuple(v) if isinstance(v, (tuple, list)) else (v, v, v, v)


def pose_m(mcp, pip, dip, conv, tcurl, taside, t1, t2x=0, t3x=0, arm_z=-18):
    mcp, pip, dip = four(mcp), four(pip), four(dip)
    extra = {ARM: {"z": arm_z}, T1: dict(t1)}
    for i, f in enumerate(FINGERS):
        b = BONES[f]
        extra[b[0]] = {"x": mcp[i]}
        extra[b[1]] = {"x": pip[i]}
        if dip[i]:
            extra[b[2]] = {"x": dip[i]}
    if t2x:
        extra[T2] = {"x": t2x}
    if t3x:
        extra[T3] = {"x": t3x}
    pose = {"thumb": {"curl": tcurl, "aside": taside}, "extra": extra}
    for i, f in enumerate(FINGERS):
        pose[f] = {"curl": 0.0, "spread": FAN3[i] * conv}
    return pose


# Tres dedos: MCP medio (lomos), PIP alto (bajan sobre el pulgar), DIP corto
# (yemas apoyadas, no enrolladas). Menique mas cerrado.
TRES = (48, 52, 54)
PIP3 = (78, 82, 84)
DIP3 = (36, 38, 40)
MENIQUE = (72, 98, 70)

T1_08 = {"x": 20, "y": -55, "z": 40}
T1_FWD = {"x": 28, "y": -48, "z": 52}
T1_PEEK = {"x": 16, "y": -60, "z": 48}

CASES = {
    "00_actual": None,
    "A_base08": pose_m(
        mcp=TRES + (MENIQUE[0],),
        pip=PIP3 + (MENIQUE[1],),
        dip=DIP3 + (MENIQUE[2],),
        conv=5,
        tcurl=0.55, taside=0.15,
        t1=T1_08, t2x=25, t3x=15,
    ),
    "B_abierto": pose_m(
        mcp=(42, 46, 50, 74),
        pip=(70, 74, 78, 100),
        dip=(28, 30, 32, 72),
        conv=6,
        tcurl=0.50, taside=0.10,
        t1=T1_FWD, t2x=22, t3x=12,
    ),
    "C_lomos": pose_m(
        mcp=(55, 58, 60, 78),
        pip=(88, 90, 92, 105),
        dip=(32, 34, 36, 68),
        conv=4,
        tcurl=0.48, taside=0.18,
        t1=T1_PEEK, t2x=28, t3x=18,
    ),
    "D_apoyo": pose_m(
        mcp=(50, 54, 58, 76),
        pip=(82, 86, 90, 102),
        dip=(44, 46, 48, 74),
        conv=5,
        tcurl=0.58, taside=0.08,
        t1=T1_FWD, t2x=30, t3x=10,
    ),
    "E_peek": pose_m(
        mcp=(46, 50, 54, 80),
        pip=(76, 80, 84, 108),
        dip=(30, 32, 34, 78),
        conv=7,
        tcurl=0.42, taside=0.22,
        t1={"x": 12, "y": -62, "z": 58},
        t2x=20, t3x=22,
    ),
    "F_junto": pose_m(
        mcp=(52, 52, 52, 76),
        pip=(84, 84, 84, 100),
        dip=(38, 38, 38, 70),
        conv=3,
        tcurl=0.52, taside=0.12,
        t1=T1_08, t2x=26, t3x=16,
    ),
    "G_menos_curl": pose_m(
        mcp=(40, 44, 48, 70),
        pip=(68, 72, 76, 96),
        dip=(24, 26, 28, 64),
        conv=6,
        tcurl=0.46, taside=0.20,
        t1={"x": 22, "y": -50, "z": 46},
        t2x=18, t3x=14,
    ),
    "H_e_thumb": pose_m(
        mcp=(50, 54, 58, 76),
        pip=(80, 84, 88, 102),
        dip=(34, 36, 38, 72),
        conv=5,
        tcurl=0.45, taside=-0.4,
        t1={"x": 40, "y": -40, "z": 60},
        t2x=24, t3x=8,
    ),
}


def hoja(items, out_path, cols=3, cell=300):
    lh = 22
    filas = (len(items) + cols - 1) // cols
    canvas = Image.new("RGB", (cols * cell, filas * (cell + lh)), (245, 245, 248))
    draw = ImageDraw.Draw(canvas)
    for i, (name, path) in enumerate(items):
        x, y = (i % cols) * cell, (i // cols) * (cell + lh)
        canvas.paste(
            Image.open(path).convert("RGB").resize((cell, cell), Image.LANCZOS),
            (x, y),
        )
        draw.rectangle([x, y + cell, x + cell, y + cell + lh], fill=(20, 30, 50))
        draw.text((x + 6, y + cell + 6), name, fill=(255, 255, 255))
    canvas.save(out_path)
    print("Hoja:", out_path)


def main():
    cat = json.loads((ROOT / "data" / "catalogo-lsm.json").read_text("utf-8"))
    CASES["00_actual"] = next(s for s in cat["senas"] if s["letra"] == "M")["pose"]

    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 900, "height": 950})
        time.sleep(0.3)
        viewer = page.query_selector("#viewer")
        free_camera(page)

        mano, huesos, lado = [], [], []
        if REF.exists():
            mano.append(("REF foto", REF))
            lado.append(("REF foto", REF))

        for name, data in CASES.items():
            page.evaluate(
                "(pose) => window.__LSM_CONTROLLER__.applyTestPose(pose)", data
            )
            time.sleep(0.28)
            g = page.evaluate(MEASURE_JS)
            t = page.evaluate(PULGAR_JS)
            print(
                f"{name:14s} dI={g['dI']:.2f} dM={g['dM']:.2f} dR={g['dR']:.2f} "
                f"tog={g['togIM']:.2f}/{g['togMR']:.2f} peek={g['peek']:.2f} "
                f"across={t['across4']:+.2f} frente={t['frente4']:+.2f}"
            )
            hand = page.evaluate(HAND_POS_JS)
            set_cam(page, "mano", hand)
            p_m = OUT / f"{name}_mano.png"
            viewer.screenshot(path=str(p_m))
            mano.append((name, p_m))

            p_h = OUT / f"{name}_huesos.png"
            page.screenshot(path=str(p_h))
            res = page.evaluate(PROJECT_JS, nombres_huesos())
            if "error" not in res:
                dibujar_overlay(p_h, res["pts"], p_h)
            huesos.append((name, p_h))

            set_cam(page, "lado", hand)
            p_l = OUT / f"{name}_lado.png"
            viewer.screenshot(path=str(p_l))
            lado.append((name, p_l))

        browser.close()

    hoja(mano, OUT / "_mano.png", cols=3, cell=300)
    hoja(lado, OUT / "_lado.png", cols=3, cell=300)
    hoja(huesos, OUT / "_huesos.png", cols=3, cell=300)


if __name__ == "__main__":
    main()
