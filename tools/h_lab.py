"""Banco de pruebas de la letra H sobre model2.glb.

lab.py apunta a los nodos del modelo anterior (mixamorig1...*_0NN); en model2.glb
los huesos se llaman RightHandIndex1 y compania, igual que en el catalogo.
"""
import time
from pathlib import Path

from PIL import Image, ImageDraw

import lab

ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / "tools" / "screenshots"

DEDOS = ["thumb", "index", "middle", "ring", "pinky"]
HUESOS = {
    "wrist": "RightHand",
    "fore": "RightForeArm",
    "arm": "RightArm",
    **{d: [f"RightHand{d.capitalize()}{i}" for i in range(1, 5)] for d in DEDOS},
}

MEASURE_JS = """
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
  const out = {};
  for (const n of __NAMES__) out[n] = P(n);
  return out;
}
"""


def _names():
    out = [HUESOS["wrist"], HUESOS["fore"], HUESOS["arm"]]
    for d in DEDOS:
        out.extend(HUESOS[d])
    return out


def puntos(page):
    import json

    js = MEASURE_JS.replace("__NAMES__", json.dumps(_names()))
    return page.evaluate(js)


def dist(a, b):
    return sum((a[i] - b[i]) ** 2 for i in range(3)) ** 0.5


def unidad(p):
    """Largo de la falange proximal del medio: escala de referencia de la mano."""
    return dist(p["RightHandMiddle1"], p["RightHandMiddle2"]) or 1.0


def metricas(page):
    """Medidas de la H, en milimetros del mundo (el modelo esta a escala humana)."""
    p = puntos(page)
    mm = 1000.0

    def d(a, b):
        return dist(p[a], p[b]) * mm

    return {
        # Separacion entre las yemas del indice y del medio: si es ~0 los dos
        # dedos quedan uno dentro del otro y se leen como uno solo.
        "yemas_ind_med": d("RightHandIndex4", "RightHandMiddle4"),
        "yemas_med_anu": d("RightHandMiddle4", "RightHandRing4"),
        # Ancho de la mano a la altura de los nudillos.
        "ancho_nudillos": d("RightHandIndex1", "RightHandPinky1"),
        "nud_ind_med": d("RightHandIndex1", "RightHandMiddle1"),
        # Largo del indice y del medio de nudillo a yema.
        "largo_indice": d("RightHandIndex1", "RightHandIndex4"),
        "largo_medio": d("RightHandMiddle1", "RightHandMiddle4"),
        "largo_palma": d("RightHand", "RightHandMiddle1"),
        # Pulgar: altura de la yema sobre el nudillo del indice.
        "pulgar_alto": (p["RightHandThumb4"][1] - p["RightHandIndex1"][1]) * mm,
        "pulgar_largo": d("RightHandThumb1", "RightHandThumb4"),
    }


def centro(page, huesos=None):
    """Punto medio de nudillos y yemas: sirve de cameraTarget.

    El modelo cuelga del target de la camara, asi que a la posicion mundo del
    hueso hay que sumarle el target vigente para obtener el punto a enfocar.
    """
    p = puntos(page)
    nombres = huesos or [
        "RightHandIndex1", "RightHandMiddle1", "RightHandRing1", "RightHandPinky1",
        "RightHandIndex4", "RightHandMiddle4", "RightHandRing4", "RightHandPinky4",
        "RightHandThumb3", "RightHandThumb4",
    ]
    pts = [p[n] for n in nombres if p.get(n)]
    n = len(pts) or 1
    t = page.evaluate(
        "() => { const t = document.getElementById('handViewer').getCameraTarget();"
        " return [t.x, t.y, t.z]; }"
    )
    return [sum(q[i] for q in pts) / n + t[i] for i in range(3)]


def foto(page, path, orbit="0deg 84deg 0.34m", fov="26deg"):
    c = centro(page)
    page.evaluate(
        """(a) => {
            const mv = document.getElementById('handViewer');
            mv.cameraTarget = a.target;
            mv.cameraOrbit = a.orbit;
            mv.fieldOfView = a.fov;
            mv.jumpCameraToGoal();
        }""",
        {
            "target": f"{c[0]:.4f}m {c[1]:.4f}m {c[2]:.4f}m",
            "orbit": orbit,
            "fov": fov,
        },
    )
    time.sleep(0.3)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    page.query_selector("#viewer").screenshot(path=str(path))
    img = Image.open(path)
    s = min(img.size)
    left = (img.width - s) // 2
    top = (img.height - s) // 2
    img.crop((left, top, left + s, top + s)).save(path)
    return path


# Las tres vistas que delatan la H: de frente se leen los dos dedos separados,
# desde arriba se ve si estan uno encima del otro y de lado el angulo del pulgar.
VISTAS = {
    "frente": "0deg 84deg 0.34m",
    "arriba": "0deg 20deg 0.34m",
    "lado": "80deg 84deg 0.34m",
}


def fotos(page, out_dir, nombre):
    rutas = []
    for vista, orbit in VISTAS.items():
        rutas.append((f"{nombre} {vista}", foto(page, Path(out_dir) / f"{nombre}_{vista}.png", orbit=orbit)))
    return rutas


def abre(browser_p, catalog=None):
    browser = browser_p.chromium.launch(channel="chrome", args=lab.CHROME_ARGS)
    page = lab.open_lab(browser, catalog or lab.load_catalog())
    return browser, page


def hoja(items, out_path, cols=3, cell=300):
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
    print("Hoja:", out_path, flush=True)
    return out_path
