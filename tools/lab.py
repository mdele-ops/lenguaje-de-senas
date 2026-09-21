"""Banco de pruebas: sirve practica.html con un catalogo LSM inventado al vuelo.

Intercepta js/catalogo-lsm.js y lo reemplaza por el catalogo que se le pase, asi
se pueden probar valores de rig.restCorrections y poses sin tocar los archivos
del repo ni recargar a mano.
"""
import json
import time
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data" / "catalogo-lsm.json"
SHOTS = ROOT / "tools" / "screenshots"
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=lab"
CHROME_ARGS = ["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"]

FOV = "26deg"
RADIUS = "0.42m"

# El modelo trae las dos manos riggeadas con la misma estructura; solo cambian
# los sufijos numericos de los nodos.
BONES = {
    "right": {
        "arm": "mixamorig1RightArm_033",
        "fore": "mixamorig1RightForeArm_034",
        "wrist": "mixamorig1RightHand_035",
        "thumb": [f"mixamorig1RightHandThumb{i}_0{35 + i}" for i in range(1, 5)],
        "index": [f"mixamorig1RightHandIndex{i}_0{39 + i}" for i in range(1, 5)],
        "middle": [f"mixamorig1RightHandMiddle{i}_0{43 + i}" for i in range(1, 5)],
        "ring": [f"mixamorig1RightHandRing{i}_0{47 + i}" for i in range(1, 5)],
        "pinky": [f"mixamorig1RightHandPinky{i}_0{51 + i}" for i in range(1, 5)],
    },
    "left": {
        "arm": "mixamorig1LeftArm_09",
        "fore": "mixamorig1LeftForeArm_010",
        "wrist": "mixamorig1LeftHand_011",
        "thumb": [f"mixamorig1LeftHandThumb{i}_0{11 + i}" for i in range(1, 5)],
        "index": [f"mixamorig1LeftHandIndex{i}_0{15 + i}" for i in range(1, 5)],
        "middle": [f"mixamorig1LeftHandMiddle{i}_0{19 + i}" for i in range(1, 5)],
        "ring": [f"mixamorig1LeftHandRing{i}_0{23 + i}" for i in range(1, 5)],
        "pinky": [f"mixamorig1LeftHandPinky{i}_0{27 + i}" for i in range(1, 5)],
    },
}

SIDE = "left"


def bones(side=None):
    return BONES[side or SIDE]


def load_catalog():
    return json.loads(CATALOG.read_text(encoding="utf-8"))


def save_catalog(data):
    CATALOG.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


HAND_CENTER_JS = """
() => {
  const mv = document.getElementById('handViewer');
  function getScene(m) {
    if (m.model && typeof m.model.traverse === 'function') return m.model;
    if (m.model && m.model.scene && typeof m.model.scene.traverse === 'function') return m.model.scene;
    for (const s of Object.getOwnPropertySymbols(m)) {
      const v = m[s];
      if (v && typeof v.traverse === 'function') return v;
      if (v && v.model && typeof v.model.traverse === 'function') return v.model;
      if (v && v.target && typeof v.target.traverse === 'function') return v.target;
    }
    return null;
  }
  const scene = getScene(mv);
  if (!scene) return null;
  scene.updateMatrixWorld(true);
  const bones = {};
  scene.traverse((o) => { if (o && o.name) bones[o.name] = o; });
  const names = __NAMES__;
  let n = 0, x = 0, y = 0, z = 0;
  for (const nm of names) {
    const b = bones[nm];
    if (!b || !b.matrixWorld) continue;
    const e = b.matrixWorld.elements;
    x += e[12]; y += e[13]; z += e[14]; n++;
  }
  if (!n) return null;
  const t = mv.getCameraTarget();
  return { x: x / n + t.x, y: y / n + t.y, z: z / n + t.z };
}
"""

VECTORS_JS = """
() => {
  const mv = document.getElementById('handViewer');
  function getScene(m) {
    if (m.model && typeof m.model.traverse === 'function') return m.model;
    if (m.model && m.model.scene && typeof m.model.scene.traverse === 'function') return m.model.scene;
    for (const s of Object.getOwnPropertySymbols(m)) {
      const v = m[s];
      if (v && typeof v.traverse === 'function') return v;
      if (v && v.model && typeof v.model.traverse === 'function') return v.model;
      if (v && v.target && typeof v.target.traverse === 'function') return v.target;
    }
    return null;
  }
  const scene = getScene(mv);
  scene.updateMatrixWorld(true);
  const b = {};
  scene.traverse((o) => { if (o && o.name) b[o.name] = o; });
  const P = (n) => {
    const o = b[n];
    if (!o) return null;
    const e = o.matrixWorld.elements;
    return [e[12], e[13], e[14]];
  };
  return {
    arm: P(__ARM__),
    foreArm: P(__FORE__),
    wrist: P(__WRIST__),
    thumb1: P(__THUMB1__),
    thumbTip: P(__THUMB4__),
    index1: P(__INDEX1__),
    indexTip: P(__INDEX4__),
    middle1: P(__MIDDLE1__),
    middleTip: P(__MIDDLE4__),
    ringTip: P(__RING4__),
    pinky1: P(__PINKY1__),
    pinkyTip: P(__PINKY4__),
  };
}
"""


def _fill(template, side=None):
    b = bones(side)
    repl = {
        "__ARM__": json.dumps(b["arm"]),
        "__FORE__": json.dumps(b["fore"]),
        "__WRIST__": json.dumps(b["wrist"]),
        "__THUMB1__": json.dumps(b["thumb"][0]),
        "__THUMB4__": json.dumps(b["thumb"][3]),
        "__INDEX1__": json.dumps(b["index"][0]),
        "__INDEX4__": json.dumps(b["index"][3]),
        "__MIDDLE1__": json.dumps(b["middle"][0]),
        "__MIDDLE4__": json.dumps(b["middle"][3]),
        "__RING4__": json.dumps(b["ring"][3]),
        "__PINKY1__": json.dumps(b["pinky"][0]),
        "__PINKY4__": json.dumps(b["pinky"][3]),
        # Centro de encuadre: nudillos y puntas. Sin la muñeca, que en los puños
        # arrastra la camara hacia el antebrazo y deja la mano descentrada.
        "__NAMES__": json.dumps(
            [
                b["index"][0], b["middle"][0], b["ring"][0], b["pinky"][0],
                b["thumb"][2], b["thumb"][3],
                b["index"][3], b["middle"][3], b["ring"][3], b["pinky"][3],
            ]
        ),
    }
    for k, v in repl.items():
        template = template.replace(k, v)
    return template


def sub(a, b):
    return [a[i] - b[i] for i in range(3)]


def length(v):
    return sum(c * c for c in v) ** 0.5


def norm(v):
    m = length(v) or 1.0
    return [c / m for c in v]


def cross(a, b):
    return [
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    ]


def r3(v):
    return [round(c, 3) for c in v]


def orientation(p, side=None):
    """dedos (+Y deseado), palma (+Z deseado) y antebrazo, en el espacio del visor.

    La normal palmar sale de indice->menique cruzado con la direccion de los
    dedos; en la mano izquierda ese producto apunta al reves, asi que se invierte.
    """
    dedos = norm(sub(p["middle1"], p["wrist"]))
    across = sub(p["pinky1"], p["index1"])
    palma = norm(cross(across, sub(p["middle1"], p["wrist"])))
    if (side or SIDE) == "left":
        palma = [-c for c in palma]
    antebrazo = norm(sub(p["wrist"], p["foreArm"]))
    return {"dedos": dedos, "palma": palma, "antebrazo": antebrazo}


def poll_ready(page, seconds=60):
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


def open_lab(browser, catalog, attempts=5):
    """Abre practica.html sirviendo `catalog` en lugar del embebido del repo."""
    payload = "window.LSM_CATALOG = " + json.dumps(catalog, ensure_ascii=False) + ";"
    last = None
    for attempt in range(1, attempts + 1):
        page = browser.new_page(viewport={"width": 760, "height": 760})
        page.route(
            "**/js/catalogo-lsm.js*",
            lambda route: route.fulfill(
                status=200,
                content_type="application/javascript; charset=utf-8",
                body=payload,
            ),
        )
        try:
            page.goto(URL, wait_until="networkidle", timeout=60000)
            page.wait_for_selector("#anim-info", timeout=20000, state="attached")
            if poll_ready(page):
                time.sleep(0.8)
                return page
            last = "modelo no listo"
        except Exception as err:
            last = repr(err)[:180]
        print(f"  intento {attempt}/{attempts} fallido ({last}); recargando...")
        page.close()
    raise RuntimeError(f"El modelo 3D no cargo: {last}")


def apply_pose(page, pose):
    page.evaluate("(p) => window.__LSM_CONTROLLER__.applyTestPose(p)", pose)
    time.sleep(0.35)


def vectors(page, side=None):
    return page.evaluate(_fill(VECTORS_JS, side))


def shot(page, path, orbit=f"0deg 84deg {RADIUS}", fov=FOV, side=None):
    center = page.evaluate(_fill(HAND_CENTER_JS, side))
    target = (
        f"{center['x']:.4f}m {center['y']:.4f}m {center['z']:.4f}m"
        if center
        else "-0.30m 2.36m 0.16m"
    )
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
    time.sleep(0.25)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    page.query_selector("#viewer").screenshot(path=str(path))
    img = Image.open(path)
    side = min(img.size)
    left = (img.width - side) // 2
    top = (img.height - side) // 2
    img.crop((left, top, left + side, top + side)).save(path)
    return path


def sheet(items, out_path, cols=4, cell=220):
    """items: [(etiqueta, ruta), ...]"""
    if not items:
        return
    rows = (len(items) + cols - 1) // cols
    label_h = 24
    img = Image.new("RGB", (cols * cell, rows * (cell + label_h)), (245, 245, 247))
    draw = ImageDraw.Draw(img)
    for i, (label, path) in enumerate(items):
        x, y = (i % cols) * cell, (i // cols) * (cell + label_h)
        img.paste(Image.open(path).convert("RGB").resize((cell, cell), Image.LANCZOS), (x, y))
        draw.rectangle([x, y + cell, x + cell, y + cell + label_h], fill=(20, 30, 50))
        draw.text((x + 8, y + cell + 7), str(label), fill=(255, 255, 255))
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)
    print("Hoja:", out_path)
    return out_path
