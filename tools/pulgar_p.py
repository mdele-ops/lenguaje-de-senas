"""P: la yema del pulgar tiene que TOCAR el dedo medio, no quedar separada.

Mide, sobre el esqueleto, la distancia (en palmas) de la punta del pulgar a cada
tramo del dedo medio y busca los giros del pulgar que la dejan en contacto
(~0.05-0.09 palmas: la piel se toca sin hundirse). Solo se mueve el pulgar: el
indice, el medio y la muñeca quedan como estan en el catalogo.

Uso: python _run.py pulgar_p.py base | busca [iteraciones]
"""
import copy
import json
import random
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

import search_e9 as se9
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "pulgar_p"
OUT.mkdir(parents=True, exist_ok=True)

se9.URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=pp"

CAT = json.loads((ROOT / "data" / "catalogo-lsm.json").read_text("utf-8"))
SENAS = CAT["senas"] if isinstance(CAT, dict) and "senas" in CAT else CAT


def pose_catalogo():
    for s in SENAS:
        if s.get("letra") == "P":
            return copy.deepcopy(s["pose"])
    raise SystemExit("no hay P en el catalogo")


CONTACTO_JS = """
() => {
  const mv = document.getElementById('handViewer');
  const scene = mv.model || mv.scene;
  function getScene(mv) {
    if (mv.model && typeof mv.model.traverse === 'function') return mv.model;
    if (mv.model && mv.model.scene) return mv.model.scene;
    const syms = Object.getOwnPropertySymbols(mv);
    for (const s of syms) {
      const v = mv[s];
      if (v && typeof v.traverse === 'function') return v;
      if (v && v.model && typeof v.model.traverse === 'function') return v.model;
      if (v && v.target && typeof v.target.traverse === 'function') return v.target;
    }
    return null;
  }
  const sc = getScene(mv);
  sc.updateMatrixWorld(true);
  const off = (sc.target && sc.target.position) || { x: 0, y: 0, z: 0 };
  const B = {};
  sc.traverse((o) => { if (o && o.name) B[o.name] = o; });
  const P = (n) => {
    if (!B[n]) throw new Error('falta ' + n);
    const e = B[n].matrixWorld.elements;
    return { x: e[12], y: e[13], z: e[14] };
  };
  const sub = (a, b) => ({ x: a.x-b.x, y: a.y-b.y, z: a.z-b.z });
  const dot = (a, b) => a.x*b.x + a.y*b.y + a.z*b.z;
  const len = (a) => Math.hypot(a.x, a.y, a.z);
  const seg = (p, a, b) => {
    const ab = sub(b, a), ap = sub(p, a);
    let t = dot(ap, ab) / (dot(ab, ab) || 1);
    t = Math.max(0, Math.min(1, t));
    const q = { x: a.x + ab.x*t, y: a.y + ab.y*t, z: a.z + ab.z*t };
    return { d: len(sub(p, q)), t: t };
  };
  const wrist = P('RightHand');
  const palm = len(sub(P('RightHandIndex1'), wrist)) || 1;
  const t4 = P('RightHandThumb4');
  const m = [1, 2, 3, 4].map((i) => P('RightHandMiddle' + i));
  const s = [seg(t4, m[0], m[1]), seg(t4, m[1], m[2]), seg(t4, m[2], m[3])];
  const best = s.map((x, i) => ({ d: x.d / palm, t: x.t, i: i }))
    .sort((a, b) => a.d - b.d)[0];
  // contra el indice tambien, para que el pulgar no se meta en el
  const i = [1, 2, 3, 4].map((k) => P('RightHandIndex' + k));
  const di = Math.min(seg(t4, i[0], i[1]).d, seg(t4, i[1], i[2]).d,
                      seg(t4, i[2], i[3]).d) / palm;
  return { d1: s[0].d/palm, d2: s[1].d/palm, d3: s[2].d/palm,
           best: best.d, seg: best.i, t: best.t, dIdx: di, palm: palm,
           tip: { x: t4.x - off.x, y: t4.y - off.y, z: t4.z - off.z } };
}
"""


def aplicar(page, pose):
    page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)


def pose_de(c, base):
    p = copy.deepcopy(base)
    p["thumb"] = {"curl": c["tcurl"], "aside": c["taside"]}
    ex = p.setdefault("extra", {})
    for hueso, pref in (("RightHandThumb1", "t1"), ("RightHandThumb2", "t2"),
                        ("RightHandThumb3", "t3")):
        r = {a: c.get(pref + a, 0.0) for a in "xyz" if abs(c.get(pref + a, 0.0)) > 1e-6}
        if r:
            ex[hueso] = r
        else:
            ex.pop(hueso, None)
    return p


def inicio(base):
    ex = base.get("extra", {})
    c = {"tcurl": base["thumb"]["curl"], "taside": base["thumb"]["aside"]}
    for hueso, pref in (("RightHandThumb1", "t1"), ("RightHandThumb2", "t2"),
                        ("RightHandThumb3", "t3")):
        for a in "xyz":
            c[pref + a] = ex.get(hueso, {}).get(a, 0.0)
    return c


def fotos(page, base, c0):
    """Retrato de la pose actual del catalogo y de la mejor, en tres vistas."""
    mejor = json.loads((OUT / "mejor.json").read_text("utf-8"))
    viewer = page.query_selector("#viewer")
    page.evaluate(
        """() => {
            const mv = document.getElementById('handViewer');
            mv.minCameraOrbit = 'auto 0deg 0.05m';
            mv.maxCameraOrbit = 'auto 180deg 10m';
            mv.minFieldOfView = '2deg';
        }"""
    )
    vistas = {"frente": "0deg 84deg 0.75m", "perfil": "-60deg 84deg 0.75m",
              "arriba": "0deg 40deg 0.75m"}
    for nombre, c in (("antes", c0), ("despues", mejor)):
        aplicar(page, pose_de(c, base))
        time.sleep(0.4)
        m = page.evaluate(CONTACTO_JS)
        t = "%.4fm %.4fm %.4fm" % (m["tip"]["x"], m["tip"]["y"], m["tip"]["z"])
        for vista, orbit in vistas.items():
            page.evaluate(
                """(a) => {
                    const mv = document.getElementById('handViewer');
                    mv.cameraTarget = a.t; mv.cameraOrbit = a.o;
                    mv.fieldOfView = '22deg'; mv.jumpCameraToGoal();
                }""",
                {"t": t, "o": orbit},
            )
            time.sleep(0.5)
            viewer.screenshot(path=str(OUT / f"{nombre}_{vista}.png"))
    print("fotos en", OUT)


def main():
    modo = sys.argv[1] if len(sys.argv) > 1 else "base"
    base = pose_catalogo()
    c0 = inicio(base)
    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 1100, "height": 900})
        time.sleep(0.5)

        aplicar(page, pose_de(c0, base))
        m = page.evaluate(CONTACTO_JS)
        print("BASE:", {k: round(v, 3) for k, v in m.items() if isinstance(v, float)}, "seg", m["seg"])
        if modo == "base":
            browser.close()
            return
        if modo == "foto":
            fotos(page, base, c0)
            browser.close()
            return

        random.seed(7)
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 800
        mejor = None
        for it in range(n):
            ref = mejor[1] if mejor and random.random() < 0.8 else c0
            c = dict(ref)
            esc = 1.0 if it < n * 0.4 else 0.35
            for k, w in (("tcurl", 0.3), ("taside", 0.3), ("t1x", 25), ("t1y", 25),
                         ("t1z", 25), ("t2x", 20), ("t2y", 15), ("t2z", 15),
                         ("t3x", 20), ("t3y", 10), ("t3z", 10)):
                if random.random() < 0.5:
                    c[k] = c[k] + random.gauss(0, w * esc)
            c["tcurl"] = max(0.0, min(1.0, c["tcurl"]))
            c["taside"] = max(-1.0, min(1.0, c["taside"]))
            aplicar(page, pose_de(c, base))
            m = page.evaluate(CONTACTO_JS)
            # contacto: ~0.07 palmas al medio y sin hundirse en el indice
            pos = m["seg"] + m["t"]
            reg = sum(abs(c[k] - c0[k]) / (0.3 if k in ("tcurl", "taside") else 30.0)
                      for k in c0)
            score = (abs(m["best"] - 0.07) + 2.0 * max(0.0, 0.12 - m["dIdx"])
                     + 0.4 * max(0.0, 0.5 - pos) + 0.4 * max(0.0, pos - 1.2)
                     + 0.01 * reg)
            if mejor is None or score < mejor[0]:
                mejor = (score, c, m)
                print(f"{it:4d} score={score:.3f} best={m['best']:.3f} pos={pos:.2f} "
                      f"dIdx={m['dIdx']:.2f}", flush=True)
        print(json.dumps(mejor[1], indent=1))
        (OUT / "mejor.json").write_text(json.dumps(mejor[1], indent=2), "utf-8")
        browser.close()


if __name__ == "__main__":
    main()
