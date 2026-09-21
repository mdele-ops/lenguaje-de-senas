"""Q lab 1: la forma de la Q es la G volteada hacia abajo, y ademas se mueve.

En la lamina del usuario la mano queda de canto con el pico indice-pulgar
apuntando al suelo: el indice sale del nudillo en diagonal hacia abajo y con
la yema enganchada, el pulgar cuelga por debajo separado de el, y medio,
anular y menique quedan cerrados en el puno. La flecha roja dibuja un arco
por debajo del pico que termina hacia la izquierda: el rabito de la Q.

Este primer lab solo busca la FORMA (la pose base). El arco se monta despues
sobre el ciclo de keyframes, que es lo unico que el controlador interpola.

Medidas (en pantalla, tal como las ve la camara de produccion):
  idxAng/thAng  angulo del indice y del pulgar en el plano de la pantalla;
                negativo = apuntando hacia abajo, que es lo que hace la Q.
  pico          separacion yema del indice -> yema del pulgar, en largos de
                palma. En la lamina el pico va abierto, no pinzado.
  idxHook       cuanto se cierra la yema del indice respecto a su recta.
  palmNz        normal de la palma: ~0 = mano de canto, no de frente.
  punoMax       la yema mas suelta de medio/anular/menique; si crece, algun
                dedo se quedo fuera del puno y la letra deja de leerse.
"""
import itertools
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from pose_lab_e import ARM, BONES, _GET_SCENE, free_camera, HAND_POS_JS
from pose_lab_p7 import CAM_FOV, CAM_ORBIT, CAM_TARGET, hoja
import search_e9 as se9
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "lab_q"
OUT.mkdir(parents=True, exist_ok=True)
REF = ROOT / "tools" / "screenshots" / "zoom_captura" / "ref_Q_x8.png"

se9.URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=q1"

WRIST = "mixamorig1RightHand_035"
FOREARM = "mixamorig1RightForeArm_034"
T1 = "mixamorig1RightHandThumb1_036"
T2 = "mixamorig1RightHandThumb2_037"
T3 = "mixamorig1RightHandThumb3_038"

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
  const sub = (a, b) => ({ x: a.x-b.x, y: a.y-b.y, z: a.z-b.z });
  const norm = (v) => {
    const l = Math.hypot(v.x, v.y, v.z) || 1;
    return { x: v.x/l, y: v.y/l, z: v.z/l };
  };
  const cross = (a, b) => ({
    x: a.y*b.z - a.z*b.y,
    y: a.z*b.x - a.x*b.z,
    z: a.x*b.y - a.y*b.x,
  });
  const d = (a, b) => Math.hypot(a.x-b.x, a.y-b.y, a.z-b.z);
  const ang = (v) => Math.atan2(v.y, v.x) * 180 / Math.PI;

  const wrist = P('mixamorig1RightHand_035');
  const i1 = P('mixamorig1RightHandIndex1_040');
  const i2 = P('mixamorig1RightHandIndex2_041');
  const i4 = P('mixamorig1RightHandIndex4_043');
  const m1 = P('mixamorig1RightHandMiddle1_044');
  const p1 = P('mixamorig1RightHandPinky1_052');
  const t2 = P('mixamorig1RightHandThumb2_037');
  const t4 = P('mixamorig1RightHandThumb4_039');
  const tips = {
    M: P('mixamorig1RightHandMiddle4_047'),
    R: P('mixamorig1RightHandRing4_051'),
    P: P('mixamorig1RightHandPinky4_055'),
  };
  const palm = d(wrist, i1) || 1;

  const nrm = norm(cross(sub(p1, i1), sub(m1, wrist)));
  const index = sub(i4, i1);
  const thumb = sub(t4, t2);
  const mano = sub(m1, wrist);
  const idxN = norm(index);

  // el gancho: cuanto se acorta el dedo respecto a su largo estirado
  const recto = d(i1, i2) + d(i2, P('mixamorig1RightHandIndex3_042'))
              + d(P('mixamorig1RightHandIndex3_042'), i4);

  let punoMax = 0;
  ['M','R','P'].forEach((k) => {
    punoMax = Math.max(punoMax, d(tips[k], wrist) / palm);
  });

  return {
    idxAng: ang(index), thAng: ang(thumb), manoAng: ang(mano),
    idxDown: idxN.y, thDown: norm(thumb).y,
    palmNx: nrm.x, palmNy: nrm.y, palmNz: nrm.z,
    pico: d(i4, t4) / palm,
    idxHook: 1 - d(i1, i4) / (recto || 1),
    idxScr: Math.hypot(index.x, index.y) / palm,
    thScr: Math.hypot(thumb.x, thumb.y) / palm,
    punoMax: punoMax,
    // la yema del pulgar por debajo de la del indice, como en la lamina
    thBajoIdx: (i4.y - t4.y) / palm,
  };
}
"""
)


def pose_q(
    wx=150,
    wy=0,
    wz=0,
    idx_mcp=0,
    idx_pip=0,
    idx_dip=0,
    tcurl=0.2,
    taside=0.35,
    t1y=0,
    t1z=0,
    t2x=0,
    arm_z=-18,
    arm=None,
    fore=None,
    cierre=0.95,
):
    """Arma la Q: puno cerrado, indice extendido con gancho y pulgar colgando.

    wx/wy/wz giran la muneca (wx ~150 deja los dedos apuntando al suelo, como
    en la N); idx_* son grados extra por falange del indice, para sacar la
    diagonal del nudillo y el gancho de la yema.
    """
    ex = {ARM: dict({"z": arm_z}, **(arm or {}))}
    if fore:
        ex[FOREARM] = dict(fore)
    b = BONES["index"]
    if idx_mcp:
        ex[b[0]] = {"x": idx_mcp}
    if idx_pip:
        ex[b[1]] = {"x": idx_pip}
    if idx_dip:
        ex[b[2]] = {"x": idx_dip}
    if t1y or t1z:
        ex[T1] = {k: v for k, v in (("y", t1y), ("z", t1z)) if v}
    if t2x:
        ex[T2] = {"x": t2x}

    muneca = {k: v for k, v in (("x", wx), ("y", wy), ("z", wz)) if v}
    pose = {
        "thumb": {"curl": tcurl, "aside": taside},
        "index": {"curl": 0.0},
        "middle": {"curl": cierre},
        "ring": {"curl": cierre},
        "pinky": {"curl": cierre},
        "extra": ex,
    }
    if muneca:
        pose["muneca"] = muneca
    return pose


def linea(nombre, m):
    return (
        f"{nombre:22s} idx={m['idxAng']:+7.1f} th={m['thAng']:+7.1f} "
        f"mano={m['manoAng']:+7.1f} pico={m['pico']:.2f} hook={m['idxHook']:.2f} "
        f"palmN=({m['palmNx']:+.2f},{m['palmNz']:+.2f}) puno={m['punoMax']:.2f} "
        f"thBajo={m['thBajoIdx']:+.2f}"
    )


def main():
    catalogo = json.loads((ROOT / "data" / "catalogo-lsm.json").read_text("utf-8"))
    actual = next(s for s in catalogo["senas"] if s["letra"] == "Q")["pose"]
    de_la_g = next(s for s in catalogo["senas"] if s["letra"] == "G")["pose"]

    casos = {"00_actual": actual, "01_G": de_la_g}
    # Barrido grueso de la muneca: donde queda el pico apuntando al suelo.
    for wx, wz in itertools.product((120, 150, 180), (0, 40, 80)):
        casos[f"w_x{wx}_z{wz}"] = pose_q(wx=wx, wz=wz)
    # Giro del antebrazo: pone la mano de canto sin torcer la muneca.
    for wy in (-40, 0, 40):
        casos[f"w_y{wy}"] = pose_q(wx=150, wy=wy)
    # Diagonal del indice y gancho de la yema.
    for mcp, dip in itertools.product((0, 20, 40), (0, 30)):
        casos[f"i_mcp{mcp}_dip{dip}"] = pose_q(idx_mcp=mcp, idx_dip=dip)

    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 1100, "height": 900})
        time.sleep(0.4)
        viewer = page.query_selector("#viewer")
        free_camera(page)

        prod, cerca = [], []
        if REF.exists():
            prod.append(("REF lamina", REF))
            cerca.append(("REF lamina", REF))

        for nombre, pose in casos.items():
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
            time.sleep(0.3)
            print(" ", linea(nombre, page.evaluate(MEASURE_JS)))

            page.evaluate(
                """(a) => {
                    const mv = document.getElementById('handViewer');
                    mv.cameraTarget = a.t;
                    mv.cameraOrbit = a.orbit;
                    mv.fieldOfView = a.fov;
                    mv.jumpCameraToGoal();
                }""",
                {"t": CAM_TARGET, "orbit": CAM_ORBIT, "fov": CAM_FOV},
            )
            time.sleep(0.25)
            path = OUT / f"{nombre}.png"
            viewer.screenshot(path=str(path))
            prod.append((nombre, path))

            mano = page.evaluate(HAND_POS_JS)
            page.evaluate(
                """(a) => {
                    const mv = document.getElementById('handViewer');
                    mv.cameraTarget = a.t;
                    mv.cameraOrbit = a.orbit;
                    mv.fieldOfView = a.fov;
                    mv.jumpCameraToGoal();
                }""",
                {
                    "t": "%.3fm %.3fm %.3fm" % (mano["x"], mano["y"] - 0.02, mano["z"]),
                    "orbit": "0deg 82deg 0.55m",
                    "fov": "26deg",
                },
            )
            time.sleep(0.25)
            zoom = OUT / f"{nombre}_zoom.png"
            viewer.screenshot(path=str(zoom))
            cerca.append((nombre, zoom))

        browser.close()

    hoja(prod, OUT / "_produccion.png", cols=5, cell=320, caja=(200, 60, 470, 330))
    hoja(cerca, OUT / "_cerca.png", cols=5, cell=320)
    (OUT / "_casos.json").write_text(json.dumps(casos, indent=2), "utf-8")


if __name__ == "__main__":
    main()
