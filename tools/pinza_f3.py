"""F: acercamiento a la pinza para elegir entre los candidatos del barrido.

La distancia entre huesos de punta no dice si la piel se toca o se hunde: el
hueso Thumb4/Index4 esta dentro de la yema. Asi que aqui se encuadra la camara
sobre el punto medio de las dos puntas y se sacan tres vistas por candidato.
"""
import math
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from junta_f import PINZA_JS, informe
from lab_e2 import MARCO_JS, abrir, hoja, orbita, preparar, recorte

OUT = Path(__file__).resolve().parents[1] / "tools" / "screenshots" / "pinza_f3"
T1 = "RightHandThumb1"

VISTAS = {
    "pinza": (1.0, 0.0, -0.35),   # de frente, algo desde el lado del pulgar
    "arriba": (0.5, 0.75, -0.3),  # mirando el hueco desde las puntas
    "canto": (0.2, 0.0, -0.97),   # de perfil, para ver si se cruzan
}


def pose(tc, ta, ic, isp, t1z):
    return {
        "thumb": {"curl": tc, "aside": ta},
        "index": {"curl": ic, "spread": isp},
        "middle": {"curl": 0.0, "spread": 3},
        "ring": {"curl": 0.0, "spread": 4},
        "pinky": {"curl": 0.0, "spread": 6},
        "extra": {T1: {"z": t1z}},
    }


# candidatos ordenados por hueco entre puntas, del mas cerrado al mas abierto
CANDIDATOS = {
    "a_031": (0.5, -0.2, 0.55, 16, 50),
    "b_038": (0.35, 0.4, 0.55, 16, 50),
    "c_074": (0.5, 0.0, 0.55, 16, 50),
    "d_087": (0.35, 0.6, 0.55, 16, 50),
    "e_089": (0.5, -0.2, 0.55, 8, 50),
    "f_093": (0.35, 0.4, 0.55, 8, 50),
    "g_116": (0.35, -0.2, 0.55, 0, 30),
    "h_261": (0.2, None, 0.5, 8, 30),  # la F de hoy, como referencia
}

PUNTO_JS = """
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
  const P = (n) => { const e = B[n].matrixWorld.elements; return { x: e[12], y: e[13], z: e[14] }; };
  const t = P('RightHandThumb4'), i = P('RightHandIndex4');
  const off = (s.target && s.target.position) || { x: 0, y: 0, z: 0 };
  return {
    x: (t.x + i.x) / 2 - off.x,
    y: (t.y + i.y) / 2 - off.y,
    z: (t.z + i.z) / 2 - off.z,
  };
}
"""


def encuadrar(page, orbit, fov, target):
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


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    salida = {}
    with sync_playwright() as p:
        browser, page = abrir(p)
        viewer = preparar(page)
        for nombre, combo in CANDIDATOS.items():
            tc, ta, ic, isp, t1z = combo
            datos = pose(tc, 0.0, ic, isp, t1z)
            if ta is None:
                datos["thumb"] = {"curl": tc}  # la F de hoy no lleva aside
            else:
                datos["thumb"] = {"curl": tc, "aside": ta}
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", datos)
            time.sleep(0.3)
            m = page.evaluate(PINZA_JS)
            print(informe(nombre, m))
            marco = page.evaluate(MARCO_JS)
            c = page.evaluate(PUNTO_JS)
            t = "%.4fm %.4fm %.4fm" % (c["x"], c["y"], c["z"])
            for vista, pesos in VISTAS.items():
                orbit = orbita(marco, pesos, radio_palmas=2.0)
                encuadrar(page, orbit, "16deg", t)
                salida.setdefault(vista, []).append(
                    (nombre, recorte(page, viewer, OUT / f"{nombre}_{vista}.png"))
                )
        browser.close()

    for vista, imgs in salida.items():
        print("hoja:", hoja(imgs, OUT / f"_{vista}.png", cols=4, cell=340))


if __name__ == "__main__":
    main()
