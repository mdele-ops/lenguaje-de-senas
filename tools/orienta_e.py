"""Que lado de la mano se ve y hacia donde apuntan los dedos.

Antes de seguir tocando angulos hay que estar seguro de lo que muestra el
render: en las hojas de contactos los dedos de la E parecen columnas VERTICALES,
que es lo contrario de lo que dicen los angulos medidos (mcp 70, pip 88, dip 60
son un puno). Aqui se comparan tres poses inequivocas -mano abierta, puno
cerrado y la E del catalogo- desde la misma camara, y se imprime hacia donde
cae cada yema en la imagen.
"""
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from calibra_e import pose
from hoja_e import preparar, publicar, retratar
from pose_lab_e import _GET_SCENE
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "orienta_e"

# Donde cae cada punto en la imagen (NDC: x a la derecha, y hacia arriba) y de
# que lado mira la palma respecto a la camara.
PANTALLA_JS = (
    """
() => {
  const mv = document.getElementById('handViewer');
"""
    + _GET_SCENE
    + """
  const scene = getScene(mv);
  const cam = scene.camera || (scene.getCamera && scene.getCamera());
  scene.updateMatrixWorld(true); cam.updateMatrixWorld(true);
  const B = {};
  scene.traverse((o) => { if (o && o.name) B[o.name] = o; });
  const P = (n) => {
    const b = B['mixamorig1RightHand' + n];
    if (!b) return null;
    const e = b.matrixWorld.elements;
    return { x: e[12], y: e[13], z: e[14] };
  };
  const m = cam.projectionMatrix.elements, v = cam.matrixWorldInverse.elements;
  const mvp = new Array(16);
  for (let i = 0; i < 4; i++) for (let j = 0; j < 4; j++) {
    let s = 0;
    for (let k = 0; k < 4; k++) s += m[k*4+j] * v[i*4+k];
    mvp[i*4+j] = s;
  }
  const pr = (p) => {
    const w = mvp[3]*p.x + mvp[7]*p.y + mvp[11]*p.z + mvp[15];
    return {
      x: (mvp[0]*p.x + mvp[4]*p.y + mvp[8]*p.z + mvp[12]) / w,
      y: (mvp[1]*p.x + mvp[5]*p.y + mvp[9]*p.z + mvp[13]) / w,
    };
  };
  const wrist = P('_035');
  const knu = ['Index1_040','Middle1_044','Ring1_048','Pinky1_052'].map(P);
  const tip = ['Index4_043','Middle4_047','Ring4_051','Pinky4_055'].map(P);
  const t4 = P('Thumb4_039');

  const o = {};
  o.wrist = pr(wrist); o.knu = knu.map(pr); o.tip = tip.map(pr);
  o.pulgar = pr(t4);

  // normal de la palma: si su componente hacia la camara es positiva, se esta
  // viendo la cara palmar; si es negativa, el dorso
  const sub = (a, b) => ({ x: a.x-b.x, y: a.y-b.y, z: a.z-b.z });
  const cross = (a, b) => ({ x: a.y*b.z-a.z*b.y, y: a.z*b.x-a.x*b.z, z: a.x*b.y-a.y*b.x });
  const nrm = (a) => { const l = Math.hypot(a.x,a.y,a.z) || 1; return { x:a.x/l, y:a.y/l, z:a.z/l }; };
  const largo = nrm(sub(knu[0], wrist));
  const ancho = nrm(sub(knu[3], knu[0]));
  const frente = nrm(cross(largo, ancho));
  const ce = cam.matrixWorld.elements;
  const haciaCam = nrm(sub({ x: ce[12], y: ce[13], z: ce[14] }, wrist));
  o.palmaHaciaCamara = frente.x*haciaCam.x + frente.y*haciaCam.y + frente.z*haciaCam.z;
  return o;
}
"""
)

CASOS = {
    "1_abierta": {
        "thumb": {"curl": 0.0},
        "index": {"curl": 0.0}, "middle": {"curl": 0.0},
        "ring": {"curl": 0.0}, "pinky": {"curl": 0.0},
        "extra": {"mixamorig1RightArm_033": {"z": -18}},
    },
    "2_puno": {
        "thumb": {"curl": 0.9},
        "index": {"curl": 0.95}, "middle": {"curl": 0.95},
        "ring": {"curl": 0.95}, "pinky": {"curl": 0.95},
        "extra": {"mixamorig1RightArm_033": {"z": -18}},
    },
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cat = json.loads((ROOT / "data" / "catalogo-lsm.json").read_text("utf-8"))
    casos = dict(CASOS)
    casos["3_E_catalogo"] = next(x for x in cat["senas"] if x["letra"] == "E")["pose"]
    casos["4_E_calibrada_65_95_60"] = pose(0.0, -4)

    with sync_playwright() as p:
        browser, page = abrir(p)
        viewer = preparar(page)
        salida = {}
        for nombre, pz in casos.items():
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pz)
            time.sleep(0.45)
            retratar(page, viewer, nombre, OUT, salida)
            d = page.evaluate(PANTALLA_JS)
            alturas = " ".join(f"{t['y']:+.3f}" for t in d["tip"])
            nudillos = " ".join(f"{k['y']:+.3f}" for k in d["knu"])
            print(
                f"{nombre:24s} palmaHaciaCamara={d['palmaHaciaCamara']:+.2f} "
                f"muneca_y={d['wrist']['y']:+.3f} nudillos_y=[{nudillos}] "
                f"yemas_y=[{alturas}] pulgar=({d['pulgar']['x']:+.3f},{d['pulgar']['y']:+.3f})"
            )
        browser.close()

    publicar(salida, OUT, cols=3, cell=320)


if __name__ == "__main__":
    main()
