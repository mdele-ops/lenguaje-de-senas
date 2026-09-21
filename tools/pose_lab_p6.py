"""P lab 6: bajar el pulgar hasta la base del medio.

En las pruebas anteriores el pulgar sube hasta la mitad del dedo medio y cierra
el hueco: la mano parece una D con el dedo estirado, no una P. En la lamina la
yema del pulgar queda a la altura del nudillo del medio y por debajo del dedo
queda aire.

Se puntua con tBase (yema del pulgar -> nudillo del medio, cuanto mas cerca
mejor) y con hueco (distancia de la yema del pulgar a la MITAD del dedo medio,
que ahora tiene que ser grande para que no se cierre el anillo).
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
OUT = ROOT / "tools" / "screenshots" / "lab_p6"
OUT.mkdir(parents=True, exist_ok=True)

se9.URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=p6"

ORBIT = "0deg 84deg 1.40m"
FOV = "21deg"
WRIST = {"y": 45, "z": 12}

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
  const wrist = P('mixamorig1RightHand_035');
  const i1 = P('mixamorig1RightHandIndex1_040');
  const m1 = P('mixamorig1RightHandMiddle1_044');
  const m2 = P('mixamorig1RightHandMiddle2_045');
  const m3 = P('mixamorig1RightHandMiddle3_046');
  const m4 = P('mixamorig1RightHandMiddle4_047');
  const r1 = P('mixamorig1RightHandRing1_048');
  const t2 = P('mixamorig1RightHandThumb2_037');
  const t4 = P('mixamorig1RightHandThumb4_039');
  const palm = d(wrist, i1) || 1;
  return {
    tBase: d(t4, m1) / palm,     // yema del pulgar en el nudillo del medio
    tMid: d(t4, m3) / palm,      // ...y lejos de la mitad del dedo (hueco)
    tTip: d(t4, m4) / palm,
    tIdx: d(t4, i1) / palm,
    tOut: d(t4, r1) / palm,
    tRise: (t4.y - m1.y) / palm,
  };
}
"""
)


def pose_p6(tcurl, taside, t1y, t1z, t2x, mid_mcp=90, wrist=None):
    ex = {ARM: {"z": -18}, BONES["middle"][0]: {"x": mid_mcp}}
    t1 = {}
    if t1y:
        t1["y"] = t1y
    if t1z:
        t1["z"] = t1z
    if t1:
        ex[T1] = t1
    if t2x:
        ex[T2] = {"x": t2x}
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
    p += 4.0 * banda(m["tBase"], 0.00, 0.45)   # yema pegada al nudillo del medio
    p += 4.0 * banda(m["tMid"], 0.75, 9.0)     # hueco abierto bajo el dedo medio
    p += 2.0 * banda(m["tTip"], 1.00, 9.0)     # sin tocar la punta (seria una D)
    p += 1.0 * banda(m["tOut"], 0.00, 0.95)    # puno compacto
    return p


def main():
    rejilla = list(
        itertools.product(
            (0.3, 0.45, 0.6, 0.75),      # tcurl
            (-0.3, -0.1, 0.1, 0.3),      # taside
            (-40, -55, -70, -85),        # t1 y
            (0, -20),                    # t1 z
            (0, 25),                     # t2 x
        )
    )

    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 900, "height": 900})
        time.sleep(0.3)
        viewer = page.query_selector("#viewer")
        free_camera(page)

        res = []
        for k in rejilla:
            page.evaluate(
                "(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose_p6(*k)
            )
            m = page.evaluate(MEASURE_JS)
            res.append((puntuar(m), k, m))
        res.sort(key=lambda t: t[0])

        print(f"{len(rejilla)} combinaciones; mejores:")
        for s, k, m in res[:12]:
            print(
                f"  tc{k[0]:<5} as{k[1]:<5} y{k[2]:<4} z{k[3]:<4} t2{k[4]:<3} "
                f"score={s:.3f} tBase={m['tBase']:.2f} tMid={m['tMid']:.2f} "
                f"tTip={m['tTip']:.2f} tOut={m['tOut']:.2f}"
            )

        items = [("REF lamina", REF)] if REF.exists() else []
        elegidos = {}
        for s, k, m in res[:8]:
            elegidos[f"tc{k[0]}_as{k[1]}_y{k[2]}_z{k[3]}_t2{k[4]}"] = pose_p6(*k)
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
                    "t": "%.3fm %.3fm %.3fm" % (hand["x"], hand["y"] + 0.04, hand["z"]),
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
