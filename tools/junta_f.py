"""F: medir cuanto les falta a las yemas de pulgar e indice para tocarse.

Primero se leen las letras que YA tienen contacto en el catalogo (O y D) para
saber que distancia significa "yemas pegadas" en este rig; despues se mide la F
actual con la misma regla. Todo en palmas (muneca -> nudillo del medio = 1).
"""
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from lab_e2 import abrir, preparar

ROOT = Path(__file__).resolve().parents[1]

PINZA_JS = """
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
  const len = (a) => Math.hypot(a.x, a.y, a.z);
  const nor = (a) => { const l = len(a) || 1; return { x: a.x/l, y: a.y/l, z: a.z/l }; };
  const cruz = (a, b) => ({ x: a.y*b.z-a.z*b.y, y: a.z*b.x-a.x*b.z, z: a.x*b.y-a.y*b.x });
  const dist = (a, b) => len(sub(a, b));
  const grados = (u, v) =>
    Math.acos(Math.max(-1, Math.min(1, dot(nor(u), nor(v))))) * 180 / Math.PI;

  const wrist = P('RightHand');
  const t3 = P('RightHandThumb3'), t4 = P('RightHandThumb4');
  const t2 = P('RightHandThumb2'), t1 = P('RightHandThumb1');
  const i3 = P('RightHandIndex3'), i4 = P('RightHandIndex4');
  const i1 = P('RightHandIndex1'), i2 = P('RightHandIndex2');
  const kM = P('RightHandMiddle1'), kP = P('RightHandPinky1');
  const m4 = P('RightHandMiddle4'), r4 = P('RightHandRing4'), p4 = P('RightHandPinky4');
  if (!wrist || !t4 || !i4) return { error: 'no-bones' };

  const palm = dist(wrist, kM) || 1;
  const largo = nor(sub(kM, wrist));
  const ancho = nor(sub(kP, i1));
  let frente = nor(cruz(ancho, largo));
  if (dot(sub(t1, wrist), frente) < 0) frente = { x:-frente.x, y:-frente.y, z:-frente.z };
  const marco = (p) => ({
    alto: dot(sub(p, wrist), largo) / palm,
    ancho: dot(sub(p, i1), ancho) / palm,
    frente: dot(sub(p, i1), frente) / palm,
  });

  // distancia entre los dos ultimos tramos (yema contra yema, no solo puntas)
  const seg = (a, b, c, d) => {
    const u = sub(b, a), v = sub(d, c), w = sub(a, c);
    const a1 = dot(u,u), b1 = dot(u,v), c1 = dot(v,v), d1 = dot(u,w), e1 = dot(v,w);
    const den = a1*c1 - b1*b1;
    let sc, tc;
    if (Math.abs(den) < 1e-9) { sc = 0; tc = (b1 > c1 ? d1/b1 : e1/c1); }
    else { sc = (b1*e1 - c1*d1) / den; tc = (a1*e1 - b1*d1) / den; }
    sc = Math.max(0, Math.min(1, sc)); tc = Math.max(0, Math.min(1, tc));
    const p1 = { x: a.x+u.x*sc, y: a.y+u.y*sc, z: a.z+u.z*sc };
    const p2 = { x: c.x+v.x*tc, y: c.y+v.y*tc, z: c.z+v.z*tc };
    return { d: dist(p1, p2), s: sc, t: tc };
  };
  const yema = seg(t3, t4, i3, i4);

  return {
    palm: palm,
    puntas: dist(t4, i4) / palm,              // punta del pulgar <-> punta del indice
    yemas: yema.d / palm,                      // tramo distal contra tramo distal
    dondeT: yema.s, dondeI: yema.t,            // 1 = el contacto cae en la punta
    // cruce: el indice pasa por delante (+) o por detras (-) del pulgar
    frenteT: marco(t4).frente, frenteI: marco(i4).frente,
    altoT: marco(t4).alto, altoI: marco(i4).alto,
    anchoT: marco(t4).ancho, anchoI: marco(i4).ancho,
    // angulo entre las dos falanges distales: ~180 = una contra otra
    enfrentados: grados(sub(t4, t3), sub(i4, i3)),
    pulgarArriba: dot(nor(sub(t4, t1)), largo),
    // los otros tres dedos deben seguir estirados
    estirados: [
      grados(largo, sub(m4, kM)),
      grados(largo, sub(r4, P('RightHandRing1'))),
      grados(largo, sub(p4, kP)),
    ],
  };
}
"""


def informe(nombre, m):
    return (
        f"{nombre:16s} puntas={m['puntas']:.3f} yemas={m['yemas']:.3f} "
        f"(t={m['dondeT']:.2f} i={m['dondeI']:.2f}) enfrent={m['enfrentados']:.0f} "
        f"frente T/I={m['frenteT']:+.2f}/{m['frenteI']:+.2f} "
        f"alto T/I={m['altoT']:+.2f}/{m['altoI']:+.2f} "
        f"ancho T/I={m['anchoT']:+.2f}/{m['anchoI']:+.2f} "
        f"estirados={[round(a) for a in m['estirados']]}"
    )


def main():
    senas = {
        s["letra"]: s
        for s in json.loads((ROOT / "data" / "catalogo-lsm.json").read_text("utf-8"))["senas"]
    }
    with sync_playwright() as p:
        browser, page = abrir(p)
        preparar(page)
        for letra in ("F", "O", "D", "C"):
            pose = senas[letra]["pose"]
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
            time.sleep(0.35)
            m = page.evaluate(PINZA_JS)
            if m.get("error"):
                print(letra, m)
                continue
            print(informe(letra, m))
        browser.close()


if __name__ == "__main__":
    main()
