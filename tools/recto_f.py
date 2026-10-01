"""F: comprobar que medio, anular y menique quedan completamente rectos.

Mide el angulo que se quiebra en cada articulacion (nudillo, falange media y
distal) de los tres dedos levantados. Con el dedo recto los tres tramos van en
la misma direccion y los angulos son ~0; cualquier `curl` residual del catalogo
aparece aqui como grados de flexion antes de que se note a ojo en el render.
"""
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from lab_e2 import abrir, hoja, preparar, retratar

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "recto_f"

ANGULOS_JS = """
() => {
  const mv = document.getElementById('handViewer');
  let s = null;
  for (const sym of Object.getOwnPropertySymbols(mv)) {
    const v = mv[sym];
    if (v && typeof v.traverse === 'function') { s = v; break; }
    if (v && v.model && typeof v.model.traverse === 'function') { s = v.model; break; }
    if (v && v.target && typeof v.target.traverse === 'function') { s = v.target; break; }
  }
  if (!s) return { error: 'no-scene' };
  s.updateMatrixWorld(true);
  const B = {};
  s.traverse((o) => { if (o && o.name) B[o.name] = o; });
  const P = (n) => {
    const b = B[n];
    if (!b || !b.matrixWorld) return null;
    const e = b.matrixWorld.elements;
    return { x: e[12], y: e[13], z: e[14] };
  };
  const sub = (a, b) => ({ x: a.x-b.x, y: a.y-b.y, z: a.z-b.z });
  const dot = (a, b) => a.x*b.x + a.y*b.y + a.z*b.z;
  const len = (a) => Math.hypot(a.x, a.y, a.z) || 1;
  const ang = (u, v) => Math.acos(Math.max(-1, Math.min(1, dot(u,v)/(len(u)*len(v))))) * 180 / Math.PI;

  const out = {};
  ['Index', 'Middle', 'Ring', 'Pinky'].forEach((d) => {
    const p = [1,2,3,4].map((k) => P('RightHand' + d + k));
    // quiebro en cada articulacion: nudillo, falange media, falange distal
    out[d.toLowerCase()] = [
      ang(sub(p[1], p[0]), sub(p[2], p[1])),
      ang(sub(p[2], p[1]), sub(p[3], p[2])),
    ];
    // desvio total de la punta respecto a la direccion del hueso de la raiz
    out[d.toLowerCase() + '_total'] = ang(sub(p[1], p[0]), sub(p[3], p[0]));
  });
  return out;
}
"""


def informe(nombre, m):
    filas = [nombre]
    for dedo in ("middle", "ring", "pinky"):
        a, b = m[dedo]
        filas.append(
            f"  {dedo:7s} nudillo->media={a:5.1f}deg  media->distal={b:5.1f}deg  "
            f"total={m[dedo + '_total']:5.1f}deg"
        )
    return "\n".join(filas)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    catalogo = json.loads((ROOT / "data" / "catalogo-lsm.json").read_text("utf-8"))
    pose = next(s for s in catalogo["senas"] if s["letra"] == "F")["pose"]

    with sync_playwright() as p:
        browser, page = abrir(p)
        viewer = preparar(page)
        page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
        time.sleep(0.6)
        m = page.evaluate(ANGULOS_JS)
        if m.get("error"):
            raise SystemExit(m)
        print(informe("F del catalogo", m))

        salida = {}
        retratar(page, viewer, "F", OUT, salida)
        browser.close()

    for vista, imgs in salida.items():
        print("hoja:", hoja(imgs, OUT / f"_{vista}.png", cols=1, cell=520))


if __name__ == "__main__":
    main()
