"""P lab 4: el pulgar. En la lamina solo asoma la yema entre indice y medio.

Con el pulgar abierto (taside alto) la mano se convierte en una pala y se pierde
el puno compacto de la letra. Lo que se busca es la yema del pulgar apoyada
contra la falange del medio, justo en el hueco que deja el indice: se mide la
distancia punta-del-pulgar -> falange media del dedo medio (tPip) y cuanto
sobresale el pulgar del contorno del puno (tOut).
"""
import itertools
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from pose_lab_e import ARM, BONES, HAND_POS_JS, T1, T2, T3, _GET_SCENE, free_camera
from pose_lab_p import REF
from pose_lab_p3 import hoja_comparativa
import search_e9 as se9
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "lab_p4"
OUT.mkdir(parents=True, exist_ok=True)

se9.URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=p4"

ORBIT = "0deg 84deg 1.40m"
FOV = "21deg"

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
  const seg = (p, a, b) => {
    const ax = b.x-a.x, ay = b.y-a.y, az = b.z-a.z;
    const px = p.x-a.x, py = p.y-a.y, pz = p.z-a.z;
    const l2 = ax*ax+ay*ay+az*az || 1;
    let t = (px*ax+py*ay+pz*az)/l2;
    t = Math.max(0, Math.min(1, t));
    return Math.hypot(p.x-(a.x+ax*t), p.y-(a.y+ay*t), p.z-(a.z+az*t));
  };
  const wrist = P('mixamorig1RightHand_035');
  const i1 = P('mixamorig1RightHandIndex1_040');
  const i2 = P('mixamorig1RightHandIndex2_041');
  const i4 = P('mixamorig1RightHandIndex4_043');
  const m1 = P('mixamorig1RightHandMiddle1_044');
  const m2 = P('mixamorig1RightHandMiddle2_045');
  const m4 = P('mixamorig1RightHandMiddle4_047');
  const r1 = P('mixamorig1RightHandRing1_048');
  const t2 = P('mixamorig1RightHandThumb2_037');
  const t4 = P('mixamorig1RightHandThumb4_039');
  const palm = d(wrist, i1) || 1;
  return {
    // yema del pulgar apoyada en la falange proximal del medio
    tPip: seg(t4, m1, m2) / palm,
    // y metida en el hueco del indice, no por fuera
    tIdxProx: seg(t4, i1, i2) / palm,
    // cuanto se aleja el pulgar del eje muneca-nudillo del anular: si crece
    // mucho el puno deja de ser compacto y la mano parece una pala
    tOut: d(t4, r1) / palm,
    tLen: d(t2, t4) / palm,
    // la yema tiene que quedar por encima del nudillo del indice (asomar)
    tRise: (t4.y - i1.y) / palm,
    idxLen: d(i1, i4) / palm,
    midTip: d(m1, m4) / palm,
  };
}
"""
)

WRIST = {"y": 45, "z": 12}


def pose_p4(tcurl, taside, t1y, t2x, t3x=0, mid_mcp=90, wrist=None):
    ex = {
        ARM: {"z": -18},
        BONES["middle"][0]: {"x": mid_mcp},
    }
    if t1y:
        ex[T1] = {"y": t1y}
    if t2x:
        ex[T2] = {"x": t2x}
    if t3x:
        ex[T3] = {"x": t3x}
    return {
        "thumb": {"curl": tcurl, "aside": taside},
        "index": {"curl": 0.0, "spread": 4},
        "middle": {"curl": 0.0, "spread": -4},
        "ring": {"curl": 0.95},
        "pinky": {"curl": 0.95},
        "muneca": dict(wrist or WRIST),
        "extra": ex,
    }


def banda(v, lo, hi):
    if v < lo:
        return lo - v
    if v > hi:
        return v - hi
    return 0.0


def puntuar(m):
    p = 0.0
    # la yema tocando la falange del medio es lo que define la K/P
    p += 5.0 * banda(m["tPip"], 0.05, 0.30)
    # sin que el pulgar se despegue del puno
    p += 2.0 * banda(m["tOut"], 0.60, 1.05)
    # y asomando por encima del nudillo del indice
    p += 2.0 * banda(m["tRise"], 0.05, 0.55)
    return p


def main():
    rejilla = list(
        itertools.product(
            (0.1, 0.25, 0.4, 0.55),  # tcurl
            (0.0, 0.2, 0.4, 0.6),  # taside
            (0, -20, -40),  # t1 y
            (0, 20, 40),  # t2 x
        )
    )

    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 900, "height": 900})
        time.sleep(0.3)
        viewer = page.query_selector("#viewer")
        free_camera(page)

        res = []
        for tcurl, taside, t1y, t2x in rejilla:
            pose = pose_p4(tcurl, taside, t1y, t2x)
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
            m = page.evaluate(MEASURE_JS)
            res.append((puntuar(m), (tcurl, taside, t1y, t2x), m))
        res.sort(key=lambda t: t[0])

        print(f"{len(rejilla)} combinaciones de pulgar; mejores:")
        for s, k, m in res[:12]:
            print(
                f"  tc{k[0]:<5} as{k[1]:<4} y{k[2]:<4} t2x{k[3]:<3} "
                f"score={s:.3f} tPip={m['tPip']:.2f} tIdx={m['tIdxProx']:.2f} "
                f"tOut={m['tOut']:.2f} tRise={m['tRise']:+.2f}"
            )

        items = [("REF lamina", REF)] if REF.exists() else []
        elegidos = {}
        for s, k, m in res[:8]:
            nombre = f"tc{k[0]}_as{k[1]}_y{k[2]}_t2{k[3]}"
            elegidos[nombre] = pose_p4(*k)
        for name, pose in elegidos.items():
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
            time.sleep(0.3)
            hand = page.evaluate(HAND_POS_JS)
            page.evaluate(
                """(a) => {
                    const mv = document.getElementById('handViewer');
                    mv.cameraTarget = a.t;
                    mv.cameraOrbit = a.orbit;
                    mv.fieldOfView = a.fov;
                    mv.jumpCameraToGoal();
                }""",
                {
                    "t": "%.3fm %.3fm %.3fm"
                    % (hand["x"], hand["y"] + 0.04, hand["z"]),
                    "orbit": ORBIT,
                    "fov": FOV,
                },
            )
            time.sleep(0.15)
            path = OUT / f"{name}.png"
            viewer.screenshot(path=str(path))
            items.append((name, path))

        browser.close()

    hoja_comparativa(items, OUT / "_comparativa.png", cols=3, cell=330)
    (OUT / "_casos.json").write_text(json.dumps(elegidos, indent=2), "utf-8")


if __name__ == "__main__":
    main()
