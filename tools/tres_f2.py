"""F: que eje del rig mueve un dedo de lado (abduccion) y cuanto.

`spread` gira el eje z de la falange proximal y en este rig eso casi no separa
los dedos (mueve poco de lado y gira el dedo sobre si mismo). Aqui se prueba
grado a grado cada eje disponible en la raiz y en la falange media de medio,
anular y menique, y se anota cuanto se desplaza la punta de lado, cuanto sube o
baja, y si se mantiene la pinza.
"""
import time

from playwright.sync_api import sync_playwright

from lab_e2 import abrir, preparar
from tres_f import BASE, TRES_JS

PUNTAS_JS = """
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
  const sub = (a, b) => ({ x: a.x-b.x, y: a.y-b.y, z: a.z-b.z });
  const dot = (a, b) => a.x*b.x + a.y*b.y + a.z*b.z;
  const len = (a) => Math.hypot(a.x, a.y, a.z);
  const nor = (a) => { const l = len(a) || 1; return { x: a.x/l, y: a.y/l, z: a.z/l }; };
  const cruz = (a, b) => ({ x: a.y*b.z-a.z*b.y, y: a.z*b.x-a.x*b.z, z: a.x*b.y-a.y*b.x });

  const wrist = P('RightHand'), kI = P('RightHandIndex1'), kM = P('RightHandMiddle1');
  const kP = P('RightHandPinky1'), t1 = P('RightHandThumb1');
  const palm = len(sub(kM, wrist)) || 1;
  const largo = nor(sub(kM, wrist));
  const ancho = nor(sub(kP, kI));
  let frente = nor(cruz(ancho, largo));
  if (dot(sub(t1, wrist), frente) < 0) frente = { x:-frente.x, y:-frente.y, z:-frente.z };
  const marco = (p) => ({
    alto: dot(sub(p, wrist), largo) / palm,
    ancho: dot(sub(p, kI), ancho) / palm,
    frente: dot(sub(p, kI), frente) / palm,
  });
  const out = {};
  ['Index', 'Middle', 'Ring', 'Pinky'].forEach((d) => {
    out[d] = marco(P('RightHand' + d + '4'));
  });
  return out;
}
"""


def con_extra(hueso, eje, grados):
    p = {k: (dict(v) if isinstance(v, dict) else v) for k, v in BASE.items()}
    p["extra"] = {"RightHandThumb1": {"z": 50}, hueso: {eje: grados}}
    return p


def main():
    with sync_playwright() as p:
        browser, page = abrir(p)
        preparar(page)

        def medir(pose):
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
            time.sleep(0.18)
            return page.evaluate(PUNTAS_JS), page.evaluate(TRES_JS)

        base, baseg = medir(BASE)
        print("base: puntas ancho/alto " + " ".join(
            f"{d}={base[d]['ancho']:+.3f}/{base[d]['alto']:+.2f}"
            for d in ("Index", "Middle", "Ring", "Pinky")
        ))
        print("base: huecos distales medio-anular=%.3f anular-menique=%.3f pinza=%.3f"
              % (baseg["mr"]["distal"], baseg["rp"]["distal"], baseg["pinza"]))

        print("\nsensibilidad (cambio de la punta por cada 10 grados):")
        for dedo in ("Middle", "Ring", "Pinky"):
            for hueso in (f"RightHand{dedo}1", f"RightHand{dedo}2"):
                for eje in ("y", "z"):
                    m, g = medir(con_extra(hueso, eje, 10))
                    d = m[dedo]
                    print(
                        f"  {hueso:20s} {eje} +10  ancho {d['ancho'] - base[dedo]['ancho']:+.3f} "
                        f"alto {d['alto'] - base[dedo]['alto']:+.3f} "
                        f"frente {d['frente'] - base[dedo]['frente']:+.3f} "
                        f"| mr={g['mr']['distal']:.3f} rp={g['rp']['distal']:.3f}"
                    )
        browser.close()


if __name__ == "__main__":
    main()
