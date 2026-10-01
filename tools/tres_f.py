"""F: juntar medio, anular y menique sin perder la pinza ni fundirlos en un bloque.

Mide la separacion entre dedos vecinos tramo a tramo (falange media y distal),
el escalon de las puntas y, a la vez, la distancia de la pinza pulgar-indice: el
`nudillos` del rig acerca las cuatro raices, asi que tocar los tres dedos tambien
mueve el indice y puede abrir el circulo de la letra.
"""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from lab_e2 import abrir, preparar

ROOT = Path(__file__).resolve().parents[1]

TRES_JS = """
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
  const seg = (a, b, c, d) => {
    const u = sub(b, a), v = sub(d, c), w = sub(a, c);
    const a1 = dot(u,u), b1 = dot(u,v), c1 = dot(v,v), d1 = dot(u,w), e1 = dot(v,w);
    const den = a1*c1 - b1*b1;
    let sc, tc;
    if (Math.abs(den) < 1e-9) { sc = 0; tc = (b1 > c1 ? d1/b1 : e1/c1); }
    else { sc = (b1*e1 - c1*d1) / den; tc = (a1*e1 - b1*d1) / den; }
    sc = Math.max(0, Math.min(1, sc)); tc = Math.max(0, Math.min(1, tc));
    return dist({ x: a.x+u.x*sc, y: a.y+u.y*sc, z: a.z+u.z*sc },
                { x: c.x+v.x*tc, y: c.y+v.y*tc, z: c.z+v.z*tc });
  };

  const D = (d) => [1,2,3,4].map((k) => P('RightHand' + d + k));
  const I = D('Index'), M = D('Middle'), R = D('Ring'), Pk = D('Pinky');
  const wrist = P('RightHand');
  const t4 = P('RightHandThumb4'), t1 = P('RightHandThumb1');
  const palm = dist(wrist, M[0]) || 1;
  const largo = nor(sub(M[0], wrist));
  const ancho = nor(sub(Pk[0], I[0]));
  let frente = nor(cruz(ancho, largo));
  if (dot(sub(t1, wrist), frente) < 0) frente = { x:-frente.x, y:-frente.y, z:-frente.z };
  const alto = (p) => dot(sub(p, wrist), largo) / palm;

  const par = (A, C) => ({
    media: seg(A[1], A[2], C[1], C[2]) / palm,   // falange media contra media
    distal: seg(A[2], A[3], C[2], C[3]) / palm,  // falange distal contra distal
    punta: dist(A[3], C[3]) / palm,
  });

  return {
    palm: palm,
    im: par(I, M), mr: par(M, R), rp: par(R, Pk),
    // altura de cada punta (1 = fila de nudillos): el escalon que se ve de frente
    puntasAlto: [I[3], M[3], R[3], Pk[3]].map(alto),
    raices: [I[0], M[0], R[0], Pk[0]].map((p) => dot(sub(p, I[0]), ancho) / palm),
    // la pinza, para no romperla al mover las raices
    pinza: dist(t4, I[3]) / palm,
  };
}
"""


def informe(nombre, m):
    a = m["puntasAlto"]
    return (
        f"{nombre:28s} medio-anular={m['mr']['media']:.3f}/{m['mr']['distal']:.3f} "
        f"anular-menique={m['rp']['media']:.3f}/{m['rp']['distal']:.3f} "
        f"indice-medio={m['im']['media']:.3f} "
        f"puntas alto=[{a[1]:+.2f} {a[2]:+.2f} {a[3]:+.2f}] "
        f"pinza={m['pinza']:.3f}"
    )


BASE = {
    "thumb": {"curl": 0.45, "aside": -0.1},
    "index": {"curl": 0.52, "spread": 14},
    "middle": {"curl": 0.0, "spread": 3},
    "ring": {"curl": 0.0, "spread": 4},
    "pinky": {"curl": 0.0, "spread": 6},
    "extra": {"RightHandThumb1": {"z": 50}},
}


def variar(**cambios):
    """Copia de la F actual con los spreads/nudillos/largo que se pidan."""
    p = {k: (dict(v) if isinstance(v, dict) else v) for k, v in BASE.items()}
    p["extra"] = {"RightHandThumb1": {"z": 50}}
    for dedo in ("middle", "ring", "pinky"):
        if dedo in cambios:
            p[dedo]["spread"] = cambios[dedo]
    if "nudillos" in cambios:
        p["nudillos"] = cambios["nudillos"]
    if "largo" in cambios:
        p["largo"] = cambios["largo"]
    return p


CASOS = {
    "0 F de ahora": variar(),
    "1 spread 0": variar(middle=0, ring=0, pinky=0),
    "2 spread en abanico al reves": variar(middle=-2, ring=-4, pinky=-8),
    "3 spread -4/-8/-14": variar(middle=-4, ring=-8, pinky=-14),
    "4 nudillos 0.2": variar(nudillos=0.2),
    "5 nudillos 0.35": variar(nudillos=0.35),
    "6 nudillos 0.5": variar(nudillos=0.5),
    "7 nud 0.35 + spread 0": variar(nudillos=0.35, middle=0, ring=0, pinky=0),
    "8 nud 0.35 + largo": variar(nudillos=0.35, middle=0, ring=0, pinky=0,
                                 largo={"pinky": 1.05, "ring": 1.02}),
}


def main():
    with sync_playwright() as p:
        browser, page = abrir(p)
        preparar(page)
        for nombre, pose in CASOS.items():
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
            time.sleep(0.25)
            m = page.evaluate(TRES_JS)
            if m.get("error"):
                raise SystemExit(m)
            print(informe(nombre, m))
            if nombre.startswith("0"):
                print("    raices (en palmas desde el nudillo del indice):",
                      [round(r, 3) for r in m["raices"]])
        browser.close()


if __name__ == "__main__":
    main()
