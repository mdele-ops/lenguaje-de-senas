"""P: mide el hueco REAL entre la piel del pulgar y la del dedo medio.

pulgar_p.py mide sobre el esqueleto (punta del hueso a eje del dedo), y eso no
dice nada del grosor: con 0.07 palmas entre huesos aun puede verse separado.
Aqui se leen los vertices de la malla con el skinning aplicado y se mide la
distancia minima entre los vertices del pulgar (huesos Thumb2-4) y los del
dedo medio (Middle1-3), en metros y en palmas. 0 o negativo = se tocan.

Uso: python _run.py piel_p.py [catalogo | json_con_pose]
"""
import copy
import json
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

import search_e9 as se9
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
se9.URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=piel"

CAT = json.loads((ROOT / "data" / "catalogo-lsm.json").read_text("utf-8"))
SENAS = CAT["senas"] if isinstance(CAT, dict) and "senas" in CAT else CAT

PIEL_JS = """
() => {
  const mv = document.getElementById('handViewer');
  function getScene(mv) {
    if (mv.model && typeof mv.model.traverse === 'function') return mv.model;
    if (mv.model && mv.model.scene) return mv.model.scene;
    for (const s of Object.getOwnPropertySymbols(mv)) {
      const v = mv[s];
      if (v && typeof v.traverse === 'function') return v;
      if (v && v.model && typeof v.model.traverse === 'function') return v.model;
    }
    return null;
  }
  const sc = getScene(mv);
  sc.updateMatrixWorld(true);
  const meshes = [];
  sc.traverse((o) => { if (o.isSkinnedMesh) meshes.push(o); });
  const nombre = (b) => b.name.replace(/^mixamorig\\d*/, '').replace(/_\\d+$/, '');
  const pulgar = [], medio = [], indice = [], punta = [];
  const v = { x: 0, y: 0, z: 0 };
  let wrist = null, idx1 = null;
  sc.traverse((o) => {
    const n = o.name && o.name.replace(/^mixamorig\\d*/, '').replace(/_\\d+$/, '');
    if (n === 'RightHand') wrist = o;
    if (n === 'RightHandIndex1') idx1 = o;
  });
  const pos = (o) => { const e = o.matrixWorld.elements; return [e[12], e[13], e[14]]; };
  const w = pos(wrist), i1 = pos(idx1);
  const palm = Math.hypot(i1[0]-w[0], i1[1]-w[1], i1[2]-w[2]);
  for (const m of meshes) {
    const g = m.geometry;
    const si = g.attributes.skinIndex, sw = g.attributes.skinWeight;
    if (!si || !sw || !m.getVertexPosition) continue;
    const bones = m.skeleton.bones.map(nombre);
    const tmp = new (m.position.constructor)();
    for (let i = 0; i < g.attributes.position.count; i++) {
      const acum = {};
      for (let k = 0; k < 4; k++) {
        const b = bones[si.getComponent(i, k)];
        acum[b] = (acum[b] || 0) + sw.getComponent(i, k);
      }
      const suma = (re) => Object.keys(acum).filter((b) => re.test(b))
        .reduce((s, b) => s + acum[b], 0);
      const tp = suma(/^RightHandThumb[234]$/);
      const tpPunta = suma(/^RightHandThumb[34]$/);
      const md = suma(/^RightHandMiddle[123]$/);
      const ix = suma(/^RightHandIndex[123]$/);
      if (tp < 0.6 && md < 0.6 && ix < 0.6) continue;
      m.getVertexPosition(i, tmp);
      tmp.applyMatrix4(m.matrixWorld);
      const p = [tmp.x, tmp.y, tmp.z];
      if (tp >= 0.6) { pulgar.push(p); if (tpPunta >= 0.6) punta.push(p); }
      else if (md >= 0.6) medio.push(p);
      else if (ix >= 0.6) indice.push(p);
    }
  }
  const minD = (A, B) => {
    let best = 1e9, pa = null, pb = null;
    for (const a of A) for (const b of B) {
      const d = Math.hypot(a[0]-b[0], a[1]-b[1], a[2]-b[2]);
      if (d < best) { best = d; pa = a; pb = b; }
    }
    return { d: best, a: pa, b: pb };
  };
  const hueso = (n) => { let r = null; sc.traverse((o) => { if (o.name && o.name.replace(/^mixamorig\d*/, '').replace(/_\d+$/, '') === n) r = o; }); return pos(r); };
  const T4 = hueso('RightHandThumb4'), T3 = hueso('RightHandThumb3');
  const M = [1,2,3,4].map((k) => hueso('RightHandMiddle' + k));
  const dd = (a, b) => Math.hypot(a[0]-b[0], a[1]-b[1], a[2]-b[2]) / palm;
  const pm0 = minD(pulgar, medio);
  const dv = punta.map((a) => { let b = 1e9; for (const q of medio) { const d = Math.hypot(a[0]-q[0], a[1]-q[1], a[2]-q[2]); if (d < b) b = d; } return b; }).sort((x, y) => x - y);
  const cerca = (mm) => dv.filter((d) => d <= mm / 1000).length;
  const area = { mm2: cerca(2), mm4: cerca(4), mm6: cerca(6), mm10: cerca(10), k15: dv.slice(0, 15).reduce((s, v) => s + v, 0) / 15 * 1000 };
  const contacto = { aT4: dd(pm0.a, T4), aT3: dd(pm0.a, T3),
                     bM2: dd(pm0.b, M[1]), bM3: dd(pm0.b, M[2]), bM4: dd(pm0.b, M[3]), bM1: dd(pm0.b, M[0]),
                     largoT4: dd(T4, T3) };
  const pm = minD(pulgar, medio), pi = minD(pulgar, indice), pp = minD(punta, medio);
  return { nPulgar: pulgar.length, nMedio: medio.length, nIndice: indice.length,
           palm: palm, gapMedio: pm.d, gapMedioPalmas: pm.d / palm,
           contacto: contacto, area: area, gapPuntaMedio: pp.d, nPunta: punta.length, gapIndice: pi.d, gapIndicePalmas: pi.d / palm };
}
"""


def pose_de(arg):
    if arg in ("catalogo", "app"):
        for s in SENAS:
            if s.get("letra") == "P":
                return copy.deepcopy(s["pose"])
        raise SystemExit("no hay P")
    return json.loads(Path(arg).read_text("utf-8"))


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else "catalogo"
    pose = pose_de(arg)
    with sync_playwright() as p:
        browser, page = abrir(p)
        time.sleep(0.5)
        if arg == "app":
            page.evaluate("() => window.__LSM_CONTROLLER__.mostrarSena('P')")
            time.sleep(2.8)
        else:
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
            time.sleep(0.6)
        print(json.dumps(page.evaluate(PIEL_JS), indent=1))
        browser.close()


if __name__ == "__main__":
    main()




