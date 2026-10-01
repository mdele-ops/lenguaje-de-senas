"""Utilidades de retrato para la E, sin matplotlib.

`hoja_e`/`compare_e10` arrastran `overlay_e` -> `skel_e` -> matplotlib, que no
esta instalado en el interprete embebido. Aqui va lo unico que hace falta para
comparar la pose con la foto: encuadrar la mano, recortar el visor y montar la
hoja de contactos.
"""
import math
import time
from pathlib import Path

from PIL import Image, ImageDraw

import search_e9
from pose_lab_e import free_camera

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "tools" / "screenshots" / "referencia"

# El servidor de trabajo de este equipo esta en 8006; el 8123 que usan los
# scripts viejos se quedo ocupado por un proceso colgado que acepta la conexion
# y no contesta, asi que se elige a mano el puerto que responde.
PUERTOS = (8006, 8123)


def abrir(p, puertos=PUERTOS):
    """`search_e9.abrir` contra el primer puerto que sirva la pagina."""
    ultimo = None
    for puerto in puertos:
        search_e9.URL = f"http://127.0.0.1:{puerto}/practica.html?letra=%E2%97%8B&v=e2"
        try:
            return search_e9.abrir(p)
        except Exception as err:  # puerto muerto o a medias
            ultimo = err
            print(f"  (puerto {puerto} no sirve: {type(err).__name__})")
    raise RuntimeError(f"ningun puerto sirve practica.html: {ultimo}")

# Vistas de trabajo, definidas por DONDE se pone la camara respecto a la propia
# mano: (frente, largo, ancho) son pesos sobre los ejes de la palma, o sea
# frente = cara palmar, largo = hacia los dedos, ancho = hacia el menique.
# Se hace asi porque los `cameraOrbit` fijos de los scripts viejos eran del .glb
# anterior: con model2.glb la mano sale de perfil y del tamano de un guisante.
VISTAS = {
    "frente": (1.0, 0.0, 0.0),
    "lado": (0.45, 0.0, -0.89),   # desde el lado del pulgar
    "abajo": (0.88, -0.48, 0.0),  # para ver el pulgar por debajo de las yemas
}

# Marco de la palma en coordenadas del mundo, mas el centro de la mano ya
# corregido por el desplazamiento que model-viewer le aplica a la escena.
MARCO_JS = """
() => {
  const mv = document.getElementById('handViewer');
  let s = null;
  for (const sym of Object.getOwnPropertySymbols(mv)) {
    const v = mv[sym];
    if (v && typeof v.traverse === 'function') { s = v; break; }
    if (v && v.model && typeof v.model.traverse === 'function') { s = v.model; break; }
    if (v && v.target && typeof v.target.traverse === 'function') { s = v.target; break; }
  }
  s.updateMatrixWorld(true);
  const B = {};
  s.traverse((o) => { if (o && o.name) B[o.name] = o; });
  const P = (n) => {
    const e = B[n].matrixWorld.elements;
    return { x: e[12], y: e[13], z: e[14] };
  };
  const sub = (a, b) => ({ x: a.x-b.x, y: a.y-b.y, z: a.z-b.z });
  const dot = (a, b) => a.x*b.x + a.y*b.y + a.z*b.z;
  const nor = (a) => { const l = Math.hypot(a.x,a.y,a.z) || 1; return { x: a.x/l, y: a.y/l, z: a.z/l }; };
  const cruz = (a, b) => ({ x: a.y*b.z-a.z*b.y, y: a.z*b.x-a.x*b.z, z: a.x*b.y-a.y*b.x });

  const wrist = P('RightHand'), kM = P('RightHandMiddle1');
  const kI = P('RightHandIndex1'), kP = P('RightHandPinky1');
  const largo = nor(sub(kM, wrist));
  const ancho = nor(sub(kP, kI));
  let frente = nor(cruz(ancho, largo));
  if (dot(sub(P('RightHandThumb1'), wrist), frente) < 0) {
    frente = { x: -frente.x, y: -frente.y, z: -frente.z };
  }
  const palm = Math.hypot(kM.x-wrist.x, kM.y-wrist.y, kM.z-wrist.z) || 1;
  // centro del encuadre: entre la muneca y los nudillos, un poco hacia delante
  const c = {
    x: (wrist.x + kM.x) / 2 + frente.x * palm * 0.25,
    y: (wrist.y + kM.y) / 2 + frente.y * palm * 0.25,
    z: (wrist.z + kM.z) / 2 + frente.z * palm * 0.25,
  };
  const off = (s.target && s.target.position) || { x: 0, y: 0, z: 0 };
  return {
    centro: { x: c.x - off.x, y: c.y - off.y, z: c.z - off.z },
    largo: largo, ancho: ancho, frente: frente, palm: palm,
  };
}
"""


def orbita(marco, pesos, radio_palmas=4.6):
    """`cameraOrbit` que pone la camara en la direccion pedida de la palma."""
    f, l, a = pesos
    d = {
        eje: f * marco["frente"][eje] + l * marco["largo"][eje] + a * marco["ancho"][eje]
        for eje in ("x", "y", "z")
    }
    n = math.sqrt(sum(v * v for v in d.values())) or 1.0
    d = {k: v / n for k, v in d.items()}
    theta = math.degrees(math.atan2(d["x"], d["z"]))
    phi = math.degrees(math.acos(max(-1.0, min(1.0, d["y"]))))
    return f"{theta:.2f}deg {phi:.2f}deg {marco['palm'] * radio_palmas:.4f}m"

def preparar(page):
    page.set_viewport_size({"width": 900, "height": 950})
    time.sleep(0.6)
    free_camera(page)
    return page.query_selector("#viewer")


def aplicar(page, pose, espera=0.4):
    page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
    time.sleep(espera)


def encuadrar(page, orbit, fov, target):
    # dos pasadas: model-viewer interpola el primer jumpCameraToGoal
    for _ in range(2):
        page.evaluate(
            """(a) => {
                const mv = document.getElementById('handViewer');
                mv.cameraTarget = a.t;
                mv.cameraOrbit = a.o;
                mv.fieldOfView = a.f;
                mv.jumpCameraToGoal();
            }""",
            {"t": target, "o": orbit, "f": fov},
        )
        time.sleep(0.3)


def recorte(page, viewer, destino):
    tmp = destino.with_suffix(".full.png")
    page.screenshot(path=str(tmp))
    box = viewer.bounding_box()
    img = Image.open(tmp)
    x, y = int(box["x"]), int(box["y"])
    w, h = int(box["width"]), int(box["height"])
    lado = min(w, h)
    img.crop((x + (w - lado) // 2, y, x + (w - lado) // 2 + lado, y + lado)).save(destino)
    tmp.unlink()
    return destino


def retratar(page, viewer, nombre, out, salida, vistas=VISTAS, fov="24deg"):
    marco = page.evaluate(MARCO_JS)
    c = marco["centro"]
    t = "%.4fm %.4fm %.4fm" % (c["x"], c["y"], c["z"])
    for vista, pesos in vistas.items():
        encuadrar(page, orbita(marco, pesos), fov, t)
        salida.setdefault(vista, []).append(
            (nombre, recorte(page, viewer, out / f"{nombre}_{vista}.png"))
        )


def hoja(items, out_path, cols=4, cell=320):
    lh = 22
    filas = (len(items) + cols - 1) // cols
    c = Image.new("RGB", (cols * cell, filas * (cell + lh)), (245, 245, 248))
    d = ImageDraw.Draw(c)
    for i, (n, p) in enumerate(items):
        x, y = (i % cols) * cell, (i // cols) * (cell + lh)
        c.paste(Image.open(p).convert("RGB").resize((cell, cell), Image.LANCZOS), (x, y))
        d.rectangle([x, y + cell, x + cell, y + cell + lh], fill=(20, 30, 50))
        d.text((x + 6, y + cell + 6), n, fill=(255, 255, 255))
    c.save(out_path)
    return out_path


def publicar(salida, out, refs=("E_usuario3.png", "E.png"), cols=4, cell=320):
    out.mkdir(parents=True, exist_ok=True)
    ref = [("REF " + n, REF / n) for n in refs if (REF / n).exists()]
    hechas = []
    for vista, imgs in salida.items():
        hechas.append(hoja(ref + imgs, out / f"_{vista}.png", cols=cols, cell=cell))
    return hechas
