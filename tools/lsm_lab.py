"""Utilidades compartidas para afinar poses LSM con Playwright.

Centraliza lo que antes se repetia en cada script: abrir practica.html esperando
a que el modelo 3D quede listo (el contexto WebGL de swiftshader se pierde a
veces y hay que recargar), aplicar poses y medir el esqueleto.
"""
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / "tools" / "screenshots"
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=lab"

CHROME_ARGS = ["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"]

ARM = "mixamorig1RightArm_033"
WRIST = "mixamorig1RightHand_035"
T1 = "mixamorig1RightHandThumb1_036"
T2 = "mixamorig1RightHandThumb2_037"
T3 = "mixamorig1RightHandThumb3_038"
T4 = "mixamorig1RightHandThumb4_039"

FINGER_BONES = {
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

FINGERS = ["index", "middle", "ring", "pinky"]

# Centro aproximado de la mano derecha del personaje.
HAND_TARGET = "-0.30m 2.37m 0.18m"

_GET_SCENE = """
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
"""

# Devuelve distancias normalizadas al largo de la palma:
#   dI..dP  yema de cada dedo -> yema del pulgar   (cerrar el circulo)
#   gIM..gRP yema -> yema de dedos vecinos         (dedos juntos)
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
  const wrist = pos('mixamorig1RightHand_035');
  const t4 = pos('mixamorig1RightHandThumb4_039');
  const i4 = pos('mixamorig1RightHandIndex4_043');
  const m4 = pos('mixamorig1RightHandMiddle4_047');
  const r4 = pos('mixamorig1RightHandRing4_051');
  const p4 = pos('mixamorig1RightHandPinky4_055');
  const palm = dist(wrist, pos('mixamorig1RightHandIndex1_040')) || 1;
  return {
    palm: palm,
    dI: dist(t4, i4)/palm, dM: dist(t4, m4)/palm,
    dR: dist(t4, r4)/palm, dP: dist(t4, p4)/palm,
    gIM: dist(i4, m4)/palm, gMR: dist(m4, r4)/palm, gRP: dist(r4, p4)/palm,
    reach: dist(wrist, i4)/palm,
    hole: dist(pos('mixamorig1RightHandIndex2_041'), pos('mixamorig1RightHandThumb3_038'))/palm,
  };
}
"""
)


def build_pose(
    curl=(0.50, 0.50, 0.50, 0.50),
    spread=(-4, 3, 4, 6),
    mcp=(12, 12, 12, 12),
    pip=(0, 0, 0, 0),
    dip=(0, 0, 0, 0),
    tcurl=0.46,
    taside=0.36,
    t1=(0, 28),
    t2x=-28,
    t3x=0,
    wrist=None,
    arm_z=-18,
):
    """Arma una pose del catalogo. Las tuplas van en orden index, middle, ring, pinky.

    mcp/pip/dip son grados extra de flexion sobre cada falange (eje de curl),
    para poder dar la curva del nudillo y la yema plana que pide la letra O.
    t1 es (y, z) del primer hueso del pulgar; t2x y t3x la flexion del segundo
    y tercero (con t3x se acerca la yema del pulgar a la del indice).
    """
    extra = {ARM: {"z": arm_z}}
    for i, f in enumerate(FINGERS):
        b = FINGER_BONES[f]
        if mcp[i]:
            extra[b[0]] = {"x": mcp[i]}
        if pip[i]:
            extra[b[1]] = {"x": pip[i]}
        if dip[i]:
            extra[b[2]] = {"x": dip[i]}
    extra[T1] = {"y": t1[0], "z": t1[1]}
    extra[T2] = {"x": t2x}
    if t3x:
        extra[T3] = {"x": t3x}

    pose = {
        "thumb": {"curl": tcurl, "aside": taside},
        "extra": extra,
    }
    for i, f in enumerate(FINGERS):
        pose[f] = {"curl": curl[i], "spread": spread[i]}
    pose["muneca"] = dict(wrist) if wrist else {"y": 50}
    return pose


# Recorre una rejilla de parametros dentro del navegador: aplicar pose + medir
# por cada combinacion es demasiado lento si va por IPC, asi que el bucle vive
# en la pagina y solo vuelven las metricas.
GRID_SEARCH_JS = (
    r"""
(grid) => {
  const mv = document.getElementById('handViewer');
  const ctrl = window.__LSM_CONTROLLER__;
"""
    + _GET_SCENE
    + r"""
  const scene = getScene(mv);
  if (!scene) return { error: 'no-scene' };
  const bones = {};
  scene.traverse((o) => { if (o && o.name) bones[o.name] = o; });

  const ARM = 'mixamorig1RightArm_033';
  const T1 = 'mixamorig1RightHandThumb1_036';
  const T2 = 'mixamorig1RightHandThumb2_037';
  const F = grid.fingerBones;
  const NAMES = ['index','middle','ring','pinky'];
  const FAN = [-1.5, -0.5, 0.5, 1.5];

  function pos(n) {
    const b = bones[n];
    if (!b || !b.matrixWorld) return null;
    const e = b.matrixWorld.elements;
    return { x: e[12], y: e[13], z: e[14] };
  }
  function dist(a, b) { return (a && b) ? Math.hypot(a.x-b.x, a.y-b.y, a.z-b.z) : null; }

  function measure() {
    if (scene.updateMatrixWorld) scene.updateMatrixWorld(true);
    const wrist = pos('mixamorig1RightHand_035');
    const t4 = pos('mixamorig1RightHandThumb4_039');
    const tip = NAMES.map((f) => pos(F[f][3]));
    const palm = dist(wrist, pos(F.index[0])) || 1;
    return {
      dI: dist(t4, tip[0])/palm, dM: dist(t4, tip[1])/palm,
      dR: dist(t4, tip[2])/palm, dP: dist(t4, tip[3])/palm,
      gIM: dist(tip[0], tip[1])/palm,
      gMR: dist(tip[1], tip[2])/palm,
      gRP: dist(tip[2], tip[3])/palm,
      // que tan recogida queda la mano (muneca -> yema del indice)
      reach: dist(wrist, tip[0])/palm,
      // diametro del hueco de la O (nudillo medio del indice -> nudillo del pulgar)
      hole: dist(pos(F.index[1]), pos('mixamorig1RightHandThumb3_038'))/palm,
    };
  }

  function buildPose(p) {
    const extra = { [ARM]: { z: p.armz } };
    const pose = { thumb: { curl: p.tcurl, aside: p.taside }, muneca: { y: p.wy } };
    NAMES.forEach((f, i) => {
      const b = F[f];
      extra[b[0]] = { x: p.k };
      if (p.m2) extra[b[1]] = { x: p.m2 };
      if (p.d3) extra[b[2]] = { x: p.d3 };
      pose[f] = { curl: p.c, spread: FAN[i] * p.conv };
    });
    extra[T1] = { y: p.t1y, z: p.t1z };
    extra[T2] = { x: p.t2x };
    if (p.t3x) extra['mixamorig1RightHandThumb3_038'] = { x: p.t3x };
    pose.extra = extra;
    return pose;
  }

  // Producto cartesiano sobre las claves que llegan como lista.
  const keys = Object.keys(grid.axes);
  const results = [];
  const idx = keys.map(() => 0);
  for (;;) {
    const p = Object.assign({}, grid.fixed);
    keys.forEach((key, i) => { p[key] = grid.axes[key][idx[i]]; });
    ctrl.applyTestPose(buildPose(p));
    results.push({ p: p, m: measure() });

    let j = keys.length - 1;
    while (j >= 0) {
      idx[j]++;
      if (idx[j] < grid.axes[keys[j]].length) break;
      idx[j] = 0;
      j--;
    }
    if (j < 0) break;
  }
  return { count: results.length, results: results };
}
"""
)

POSE_DEFAULTS = {
    "conv": -14,
    "c": 0.50,
    "k": 12,
    "m2": 0,
    "d3": 0,
    "tcurl": 0.46,
    "taside": 0.36,
    "t1y": 0,
    "t1z": 28,
    "t2x": -28,
    "t3x": 0,
    "wy": 50,
    "armz": -18,
}

FAN = (-1.5, -0.5, 0.5, 1.5)


def pose_from_params(p):
    """Convierte los parametros de la busqueda en una pose del catalogo."""
    q = dict(POSE_DEFAULTS)
    q.update(p)
    return build_pose(
        curl=(q["c"],) * 4,
        spread=tuple(f * q["conv"] for f in FAN),
        mcp=(q["k"],) * 4,
        pip=(q["m2"],) * 4,
        dip=(q["d3"],) * 4,
        tcurl=q["tcurl"],
        taside=q["taside"],
        t1=(q["t1y"], q["t1z"]),
        t2x=q["t2x"],
        t3x=q["t3x"],
        wrist={"y": q["wy"]},
        arm_z=q["armz"],
    )


def grid_search(page, axes, fixed=None):
    """axes: dict clave -> lista de valores. Devuelve [{p, m}, ...]."""
    grid = {
        "fingerBones": FINGER_BONES,
        "axes": axes,
        "fixed": {**POSE_DEFAULTS, **(fixed or {})},
    }
    out = page.evaluate(GRID_SEARCH_JS, grid)
    if out.get("error"):
        raise RuntimeError(out["error"])
    return out["results"]


def poll_ready(page, seconds=45):
    deadline = time.time() + seconds
    while time.time() < deadline:
        try:
            if page.evaluate(
                "() => !!(window.__LSM_CONTROLLER__ && window.__LSM_CONTROLLER__.isModelReady())"
            ):
                return True
        except Exception:
            pass
        time.sleep(0.4)
    return False


def open_ready_page(browser, viewport=(900, 900), attempts=4):
    """Abre practica.html reintentando: swiftshader pierde el contexto WebGL a
    veces al cargar model2.glb y entonces la pagina nunca queda lista."""
    last = None
    for attempt in range(1, attempts + 1):
        page = browser.new_page(viewport={"width": viewport[0], "height": viewport[1]})
        try:
            page.goto(URL, wait_until="networkidle", timeout=60000)
            page.wait_for_selector("#anim-info", timeout=20000, state="attached")
            if poll_ready(page):
                time.sleep(1.0)
                return page
            last = "modelo no listo"
        except Exception as err:
            last = repr(err)[:200]
        print(f"  intento {attempt}/{attempts} fallido ({last}); recargando...")
        page.close()
    raise RuntimeError(f"El modelo 3D no cargo a tiempo: {last}")


def apply_pose(page, pose):
    page.evaluate("(p) => window.__LSM_CONTROLLER__.applyTestPose(p)", pose)


def measure(page):
    return page.evaluate(MEASURE_JS)


def set_camera(page, target=HAND_TARGET, orbit="0deg 82deg 0.42m", fov="26deg"):
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
    time.sleep(0.2)


def out_dir(name):
    d = SHOTS / name
    d.mkdir(parents=True, exist_ok=True)
    return d
