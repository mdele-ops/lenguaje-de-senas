"""E lab 1: nudillos arriba, dedos doblados en la falange media y pulgar
atravesado por delante de la palma, con las yemas apoyadas encima.

La E no se consigue subiendo curl (eso da un puno = A/S): hay que repartir la
flexion (MCP poco, PIP mucho, DIP medio) para que las yemas bajen sobre el
pulgar dejando el escalon que hace legible la letra.
"""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_e"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=e1"

ARM = "mixamorig1RightArm_033"
T1 = "mixamorig1RightHandThumb1_036"
T2 = "mixamorig1RightHandThumb2_037"
T3 = "mixamorig1RightHandThumb3_038"

FINGERS = ["index", "middle", "ring", "pinky"]
BONES = {
    "index": [
        "mixamorig1RightHandIndex1_040",
        "mixamorig1RightHandIndex2_041",
        "mixamorig1RightHandIndex3_042",
        "mixamorig1RightHandIndex4_043",
    ],
    "middle": [
        "mixamorig1RightHandMiddle1_044",
        "mixamorig1RightHandMiddle2_045",
        "mixamorig1RightHandMiddle3_046",
        "mixamorig1RightHandMiddle4_047",
    ],
    "ring": [
        "mixamorig1RightHandRing1_048",
        "mixamorig1RightHandRing2_049",
        "mixamorig1RightHandRing3_050",
        "mixamorig1RightHandRing4_051",
    ],
    "pinky": [
        "mixamorig1RightHandPinky1_052",
        "mixamorig1RightHandPinky2_053",
        "mixamorig1RightHandPinky3_054",
        "mixamorig1RightHandPinky4_055",
    ],
}

_GET_SCENE = """
function getScene(mv) {
  if (mv.model && typeof mv.model.traverse === 'function') return mv.model;
  if (mv.model && mv.model.scene && typeof mv.model.scene.traverse === 'function') return mv.model.scene;
  const symbols = Object.getOwnPropertySymbols(mv);
  for (let i = 0; i < symbols.length; i++) {
    const v = mv[symbols[i]];
    if (v && typeof v.traverse === 'function') return v;
    if (v && v.model && typeof v.model.traverse === 'function') return v.model;
    if (v && v.target && typeof v.target.traverse === 'function') return v.target;
  }
  return null;
}
"""

# Metricas de la E, normalizadas al largo de la palma:
#   dI..dP  yema del dedo -> eje del pulgar (que tan apoyadas quedan)
#   overI.. cuanto queda la yema por ENCIMA del pulgar (positivo = encima)
#   knuck   altura del nudillo medio respecto a la yema (el escalon de la E)
#   tHoriz  que tan horizontal esta el pulgar (1 = tumbado, 0 = vertical)
MEASURE_JS = (
    """
() => {
  const mv = document.getElementById('handViewer');
"""
    + _GET_SCENE
    + """
  const scene = getScene(mv);
  if (!scene) return { error: 'no-scene' };
  if (scene.updateMatrixWorld) scene.updateMatrixWorld(true);
  const bones = {};
  scene.traverse((o) => { if (o && o.name) bones[o.name] = o; });
  function pos(n) {
    const b = bones[n];
    if (!b || !b.matrixWorld) return null;
    const e = b.matrixWorld.elements;
    return { x: e[12], y: e[13], z: e[14] };
  }
  function dist(a, b) { return (a && b) ? Math.hypot(a.x-b.x, a.y-b.y, a.z-b.z) : null; }
  // distancia de un punto al segmento del pulgar (T2-T4): la yema se apoya en
  // el cuerpo del pulgar, no necesariamente en su punta.
  function closestOnSeg(p, a, b) {
    const abx = b.x-a.x, aby = b.y-a.y, abz = b.z-a.z;
    const apx = p.x-a.x, apy = p.y-a.y, apz = p.z-a.z;
    const len2 = abx*abx + aby*aby + abz*abz || 1;
    let t = (apx*abx + apy*aby + apz*abz) / len2;
    t = Math.max(0, Math.min(1, t));
    return { x: a.x + abx*t, y: a.y + aby*t, z: a.z + abz*t };
  }
  function distSeg(p, a, b) {
    const c = closestOnSeg(p, a, b);
    return Math.hypot(p.x-c.x, p.y-c.y, p.z-c.z);
  }
  const wrist = pos('mixamorig1RightHand_035');
  const t2 = pos('mixamorig1RightHandThumb2_037');
  const t4 = pos('mixamorig1RightHandThumb4_039');
  const tips = {
    I: pos('mixamorig1RightHandIndex4_043'),
    M: pos('mixamorig1RightHandMiddle4_047'),
    R: pos('mixamorig1RightHandRing4_051'),
    P: pos('mixamorig1RightHandPinky4_055'),
  };
  const pip = {
    I: pos('mixamorig1RightHandIndex2_041'),
    M: pos('mixamorig1RightHandMiddle2_045'),
    R: pos('mixamorig1RightHandRing2_049'),
    P: pos('mixamorig1RightHandPinky2_053'),
  };
  const knuckle = {
    I: pos('mixamorig1RightHandIndex1_040'),
    M: pos('mixamorig1RightHandMiddle1_044'),
    R: pos('mixamorig1RightHandRing1_048'),
    P: pos('mixamorig1RightHandPinky1_052'),
  };
  const palm = dist(wrist, pos('mixamorig1RightHandIndex1_040')) || 1;
  const out = { palm: palm };
  ['I','M','R','P'].forEach((k) => {
    out['d'+k] = distSeg(tips[k], t2, t4) / palm;
    out['over'+k] = (tips[k].y - t2.y) / palm;
    out['knuck'+k] = (pip[k].y - tips[k].y) / palm;
    // positivo = la yema quedo por debajo del nudillo, o sea el dedo doblo
    out['fold'+k] = (knuckle[k].y - tips[k].y) / palm;
    // positivo = la yema queda DELANTE del pulgar (se apoya encima, no detras)
    out['front'+k] = (tips[k].z - closestOnSeg(tips[k], t2, t4).z) / palm;
  });
  const tdx = t4.x-t2.x, tdy = t4.y-t2.y, tdz = t4.z-t2.z;
  const tlen = Math.hypot(tdx, tdy, tdz) || 1;
  out.tHoriz = Math.hypot(tdx, tdz) / tlen;
  out.thumbTipToIndexTip = dist(t4, tips.I) / palm;
  // separacion entre yemas vecinas: en la E los cuatro dedos van juntos
  out.gIM = dist(tips.I, tips.M) / palm;
  out.gMR = dist(tips.M, tips.R) / palm;
  out.gRP = dist(tips.R, tips.P) / palm;
  return out;
}
"""
)

# Centra la camara en la mano real (su posicion cambia con el extra del brazo).
# model-viewer traslada el modelo por -cameraTarget, asi que para volver a las
# coordenadas que entiende cameraTarget hay que deshacer ese offset.
HAND_POS_JS = (
    """
() => {
  const mv = document.getElementById('handViewer');
"""
    + _GET_SCENE
    + """
  const scene = getScene(mv);
  if (scene.updateMatrixWorld) scene.updateMatrixWorld(true);
  const want = { 'mixamorig1RightHand_035': null, 'mixamorig1RightHandMiddle1_044': null };
  scene.traverse((o) => { if (o && o.name in want) want[o.name] = o; });
  const wrist = want['mixamorig1RightHand_035'];
  const knuck = want['mixamorig1RightHandMiddle1_044'];
  if (!wrist || !knuck) return null;
  const a = wrist.matrixWorld.elements;
  const b = knuck.matrixWorld.elements;
  const off = (scene.target && scene.target.position) || { x: 0, y: 0, z: 0 };
  // centro de la mano: entre muñeca y nudillo medio, para que quepan dedos y palma
  return {
    x: (a[12] + b[12]) / 2 - off.x,
    y: (a[13] + b[13]) / 2 - off.y,
    z: (a[14] + b[14]) / 2 - off.z,
  };
}
"""
)


def pose_e(
    curl=0.24,
    mcp=(6, 6, 6, 6),
    pip=(76, 76, 76, 76),
    dip=(18, 18, 18, 18),
    spread=(-3, 1, 2, 4),
    tcurl=0.74,
    taside=-0.5,
    t1=(-60, 0),
    t2x=0,
    t3x=0,
    wrist=None,
    arm_z=-18,
    extra=None,
):
    """Arma la pose de la E. Las tuplas van en orden index, middle, ring, pinky.

    mcp/pip/dip son grados extra sobre cada falange: el reparto (poco en el
    nudillo, mucho en la falange media) es lo que baja las yemas al pulgar sin
    cerrar el puno. t1 es (y, z) del primer hueso del pulgar.
    """
    ex = {ARM: {"z": arm_z}, T1: {"y": t1[0], "z": t1[1]}}
    for i, f in enumerate(FINGERS):
        b = BONES[f]
        if mcp[i]:
            ex[b[0]] = {"x": mcp[i]}
        if pip[i]:
            ex[b[1]] = {"x": pip[i]}
        if dip[i]:
            ex[b[2]] = {"x": dip[i]}
    if t2x:
        ex[T2] = {"x": t2x}
    if t3x:
        ex[T3] = {"x": t3x}
    if extra:
        for name, rot in extra.items():
            ex[name] = dict(ex.get(name, {}), **rot)

    pose = {"thumb": {"curl": tcurl, "aside": taside}, "extra": ex}
    for i, f in enumerate(FINGERS):
        pose[f] = {"curl": curl, "spread": spread[i]}
    if wrist:
        pose["muneca"] = dict(wrist)
    return pose


ACTUAL = {
    "thumb": {"curl": 0.6},
    "index": {"curl": 0.9},
    "middle": {"curl": 0.9},
    "ring": {"curl": 0.9},
    "pinky": {"curl": 0.9},
}

CASES = {
    "00_actual": ACTUAL,
    # Reparto de la flexion: cuanto PIP hace falta para que la yema baje.
    "01_pip60": pose_e(pip=(60,) * 4),
    "02_pip76": pose_e(pip=(76,) * 4),
    "03_pip92": pose_e(pip=(92,) * 4),
    "04_pip105": pose_e(pip=(105,) * 4),
    # Nudillo (MCP): con mas MCP los dedos se van hacia la palma.
    "05_mcp20_pip92": pose_e(mcp=(20,) * 4, pip=(92,) * 4),
    "06_mcp34_pip92": pose_e(mcp=(34,) * 4, pip=(92,) * 4),
    # Yema (DIP): plana o mas cerrada sobre el pulgar.
    "07_dip0": pose_e(pip=(92,) * 4, dip=(0,) * 4),
    "08_dip36": pose_e(pip=(92,) * 4, dip=(36,) * 4),
    # Pulgar: de vertical (B) a tumbado atravesando la palma.
    "09_t_y30": pose_e(pip=(92,) * 4, t1=(-30, 0)),
    "10_t_y60_z30": pose_e(pip=(92,) * 4, t1=(-60, 30)),
    "11_t_y60_z50": pose_e(pip=(92,) * 4, t1=(-60, 50)),
    "12_t_curl90": pose_e(pip=(92,) * 4, tcurl=0.9),
    "13_t_curl55": pose_e(pip=(92,) * 4, tcurl=0.55),
}


def free_camera(page):
    """practica.html limita el orbit a 1.2 m; sin soltarlo no hay primer plano."""
    page.evaluate(
        """() => {
            const mv = document.getElementById('handViewer');
            mv.minCameraOrbit = 'auto 0deg 0.05m';
            mv.maxCameraOrbit = 'auto 180deg 10m';
            mv.minFieldOfView = '2deg';
        }"""
    )


def set_cam(page, kind, hand):
    target = "%.3fm %.3fm %.3fm" % (hand["x"], hand["y"], hand["z"])
    views = {
        "prod": ("0m 2.45m 0.15m", "0deg 84deg 2.5m", "30deg"),
        "mano": (target, "0deg 82deg 0.62m", "26deg"),
        "lado": (target, "-55deg 82deg 0.62m", "26deg"),
        "arriba": (target, "0deg 45deg 0.62m", "26deg"),
    }
    t, orbit, fov = views[kind]
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


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="chrome",
            args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"],
        )
        page = browser.new_page(viewport={"width": 900, "height": 900})
        page.goto(URL, wait_until="networkidle", timeout=60000)
        page.wait_for_selector("#anim-info", timeout=20000, state="attached")

        ready = False
        for _ in range(120):
            try:
                if page.evaluate(
                    "() => !!(window.__LSM_CONTROLLER__ && window.__LSM_CONTROLLER__.isModelReady())"
                ):
                    ready = True
                    break
            except Exception:
                pass
            time.sleep(0.4)
        if not ready:
            raise RuntimeError("El modelo 3D no cargo a tiempo")
        time.sleep(1.0)

        viewer = page.query_selector("#viewer")
        free_camera(page)
        for name, data in CASES.items():
            page.evaluate(
                "(pose) => window.__LSM_CONTROLLER__.applyTestPose(pose)", data
            )
            time.sleep(0.25)
            m = page.evaluate(MEASURE_JS)
            print(
                f"{name:18s} dI={m['dI']:.3f} dM={m['dM']:.3f} dR={m['dR']:.3f} "
                f"dP={m['dP']:.3f} overM={m['overM']:+.3f} knuckM={m['knuckM']:+.3f} "
                f"tHoriz={m['tHoriz']:.2f}"
            )
            hand = page.evaluate(HAND_POS_JS)
            for view in ("mano", "lado"):
                set_cam(page, view, hand)
                viewer.screenshot(path=str(OUT_DIR / f"{name}_{view}.png"))

        browser.close()


if __name__ == "__main__":
    main()
