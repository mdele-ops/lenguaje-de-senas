"""P lab 1: la P es la K con el dedo medio tumbado hacia adelante.

En la lamina el indice sale recto hacia arriba y el medio sale casi horizontal
hacia el frente, formando escuadra; el pulgar asoma entre los dos y anular y
menique quedan cerrados. Lo que hay hoy en el catalogo ("K girada hacia abajo",
muneca x60) no se parece: cuelga toda la mano.

El medio no se tumba con curl (eso dobla las tres falanges y lo convierte en un
gancho): se rota SOLO el nudillo (MCP) y las otras dos falanges quedan rectas.
"""
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from pose_lab_e import ARM, BONES, HAND_POS_JS, T1, T2, T3, _GET_SCENE, free_camera
from pose_lab_m5 import hoja
import search_e9 as se9
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "lab_p"
OUT.mkdir(parents=True, exist_ok=True)
REF = ROOT / "tools" / "screenshots" / "referencia" / "P.png"

se9.URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=p1"

# Metricas de la P (normalizadas al largo de la palma):
#   idxUp    +1 = el indice apunta al techo
#   midFwd   +1 = el medio apunta al frente del avatar (lo que pide la lamina)
#   midUp    0  = el medio esta horizontal; +1 seria vertical como el indice
#   escuadra angulo indice-medio en grados (la lamina pide ~80-90)
#   thumbIM  que tan centrada queda la punta del pulgar entre indice y medio
#   ringHid  el anular cerrado queda por debajo del nudillo (puno)
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
  const dir = (a, b) => {
    const x = b.x-a.x, y = b.y-a.y, z = b.z-a.z;
    const l = Math.hypot(x,y,z) || 1;
    return { x: x/l, y: y/l, z: z/l };
  };
  const wrist = P('mixamorig1RightHand_035');
  const i1 = P('mixamorig1RightHandIndex1_040');
  const i4 = P('mixamorig1RightHandIndex4_043');
  const m1 = P('mixamorig1RightHandMiddle1_044');
  const m2 = P('mixamorig1RightHandMiddle2_045');
  const m4 = P('mixamorig1RightHandMiddle4_047');
  const r1 = P('mixamorig1RightHandRing1_048');
  const r4 = P('mixamorig1RightHandRing4_051');
  const p4 = P('mixamorig1RightHandPinky4_055');
  const t4 = P('mixamorig1RightHandThumb4_039');
  const palm = d(wrist, i1) || 1;
  const index = dir(i1, i4);
  const middle = dir(m1, m4);
  const dot = index.x*middle.x + index.y*middle.y + index.z*middle.z;
  return {
    idxUp: index.y,
    idxFwd: index.z,
    midFwd: middle.z,
    midUp: middle.y,
    midSide: middle.x,
    escuadra: Math.acos(Math.max(-1, Math.min(1, dot))) * 180 / Math.PI,
    // el medio tiene que salir RECTO desde el nudillo, no engancharse
    midRecto: (dir(m1, m2).x*middle.x + dir(m1, m2).y*middle.y + dir(m1, m2).z*middle.z),
    thumbTipY: (t4.y - i1.y) / palm,
    thumbIdx: d(t4, i4) / palm,
    thumbMid: d(t4, m4) / palm,
    ringHid: (r1.y - r4.y) / palm,
    pinkyHid: (r1.y - p4.y) / palm,
  };
}
"""
)

VIEWS = {
    # como se ve en la practica, con el cuerpo entero
    "prod": ("0m 2.45m 0.15m", "0deg 84deg 2.5m", "30deg"),
    # de frente al avatar
    "frente": (None, "0deg 82deg 0.60m", "26deg"),
    # de perfil: es la vista de la lamina (indice arriba, medio hacia la derecha)
    "perfil": (None, "-88deg 84deg 0.60m", "26deg"),
    "perfil2": (None, "-55deg 84deg 0.60m", "26deg"),
}


def set_cam(page, kind, hand):
    t, orbit, fov = VIEWS[kind]
    if t is None:
        t = "%.3fm %.3fm %.3fm" % (hand["x"], hand["y"], hand["z"])
    page.evaluate(
        """(a) => {
            const mv = document.getElementById('handViewer');
            mv.cameraTarget = a.t;
            mv.cameraOrbit = a.orbit;
            mv.fieldOfView = a.fov;
            mv.jumpCameraToGoal();
        }""",
        {"t": t, "orbit": orbit, "fov": fov},
    )
    time.sleep(0.12)


def pose_p(
    mid_mcp=85,
    mid_pip=0,
    idx_mcp=0,
    spread=(0, 0),
    ring=0.95,
    pinky=0.95,
    tcurl=0.25,
    taside=0.2,
    t1=None,
    t2x=0,
    t3x=0,
    wrist=None,
    arm_z=-18,
    extra=None,
):
    """Arma la P: indice recto arriba y medio tumbado al frente desde el nudillo."""
    ex = {ARM: {"z": arm_z}}
    if t1:
        ex[T1] = dict(t1)
    if t2x:
        ex[T2] = {"x": t2x}
    if t3x:
        ex[T3] = {"x": t3x}
    if idx_mcp:
        ex[BONES["index"][0]] = {"x": idx_mcp}
    if mid_mcp:
        ex[BONES["middle"][0]] = {"x": mid_mcp}
    if mid_pip:
        ex[BONES["middle"][1]] = {"x": mid_pip}
    if extra:
        for name, rot in extra.items():
            ex[name] = dict(ex.get(name, {}), **rot)
    pose = {
        "thumb": {"curl": tcurl, "aside": taside},
        "index": {"curl": 0.0, "spread": spread[0]},
        "middle": {"curl": 0.0, "spread": spread[1]},
        "ring": {"curl": ring},
        "pinky": {"curl": pinky},
        "extra": ex,
    }
    if wrist:
        pose["muneca"] = dict(wrist)
    return pose


CAT = json.loads((ROOT / "data" / "catalogo-lsm.json").read_text("utf-8"))
CASES = {
    "00_actual": next(s for s in CAT["senas"] if s["letra"] == "P")["pose"],
    "01_K": next(s for s in CAT["senas"] if s["letra"] == "K")["pose"],
    # cuanto hay que tumbar el nudillo del medio para que quede horizontal
    "A_mcp60": pose_p(mid_mcp=60),
    "B_mcp75": pose_p(mid_mcp=75),
    "C_mcp90": pose_p(mid_mcp=90),
    "D_mcp105": pose_p(mid_mcp=105),
    # el medio con un poco de PIP, por si sale demasiado rigido
    "E_mcp85_pip15": pose_p(mid_mcp=85, mid_pip=15),
    # separacion entre indice y medio
    "F_spread": pose_p(mid_mcp=90, spread=(6, -6)),
    # muneca: la lamina tiene la mano vertical, no colgando
    "G_wx-18": pose_p(mid_mcp=90, wrist={"x": -18}),
    "H_wx15": pose_p(mid_mcp=90, wrist={"x": 15}),
    "I_wy30": pose_p(mid_mcp=90, wrist={"y": 30}),
    "J_wy-30": pose_p(mid_mcp=90, wrist={"y": -30}),
    "K_wz25": pose_p(mid_mcp=90, wrist={"z": 25}),
    # pulgar asomando entre indice y medio
    "L_pulgar": pose_p(mid_mcp=90, tcurl=0.1, taside=0.35),
    "M_pulgar2": pose_p(mid_mcp=90, tcurl=0.35, taside=0.1, t1={"y": -20}),
}


def main():
    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 900, "height": 950})
        time.sleep(0.3)
        viewer = page.query_selector("#viewer")
        free_camera(page)

        hojas = {k: [] for k in VIEWS}
        if REF.exists():
            for k in hojas:
                hojas[k].append(("REF lamina", REF))

        for name, data in CASES.items():
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", data)
            time.sleep(0.3)
            m = page.evaluate(MEASURE_JS)
            print(
                f"{name:14s} idxUp={m['idxUp']:+.2f} midFwd={m['midFwd']:+.2f} "
                f"midUp={m['midUp']:+.2f} midSide={m['midSide']:+.2f} "
                f"ang={m['escuadra']:5.1f} recto={m['midRecto']:.2f} "
                f"tIdx={m['thumbIdx']:.2f} tMid={m['thumbMid']:.2f} "
                f"ring={m['ringHid']:+.2f}"
            )
            hand = page.evaluate(HAND_POS_JS)
            for view in VIEWS:
                set_cam(page, view, hand)
                path = OUT / f"{name}_{view}.png"
                viewer.screenshot(path=str(path))
                hojas[view].append((name, path))

        browser.close()

    for view, items in hojas.items():
        hoja(items, OUT / f"_{view}.png", cols=4, cell=280)
    (OUT / "_casos.json").write_text(json.dumps(CASES, indent=2), "utf-8")


if __name__ == "__main__":
    main()
