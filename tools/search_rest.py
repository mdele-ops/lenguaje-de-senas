"""Busca las rotaciones de rig.restCorrections que dejan la mano "leible":
dedos hacia arriba (+Y), palma hacia la camara (+Z) y antebrazo subiendo desde
el codo, con la mano delante del pecho (como la lamina del abecedario).

    py tools/search_rest.py left

Carga el modelo SIN correcciones para partir de la pose bind y prueba miles de
combinaciones dentro del navegador.
"""
import json
import sys

from playwright.sync_api import sync_playwright

import lab

SEARCH_JS = r"""
(spec) => {
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
  const bones = {};
  scene.traverse((o) => { if (o && o.name) bones[o.name] = o; });

  const B = spec.bones;
  const NAMES = [B.arm, B.fore, B.wrist];
  const KEY = '__BIND__' + B.wrist;

  if (!window[KEY]) {
    const snap = {};
    for (const n of NAMES) {
      const q = bones[n].quaternion;
      snap[n] = { x: q.x, y: q.y, z: q.z, w: q.w };
    }
    window[KEY] = snap;
  }
  const BIND = window[KEY];
  const DEG = Math.PI / 180;

  function reset() {
    for (const n of NAMES) {
      const b = BIND[n];
      bones[n].quaternion.set(b.x, b.y, b.z, b.w);
    }
  }
  function applyRots(name, rots) {
    const bone = bones[name];
    for (const r of rots || []) {
      const axis = r[0], deg = r[1];
      if (!deg) continue;
      if (axis === 'x') bone.rotateX(deg * DEG);
      else if (axis === 'y') bone.rotateY(deg * DEG);
      else bone.rotateZ(deg * DEG);
    }
  }
  function P(n) {
    const e = bones[n].matrixWorld.elements;
    return [e[12], e[13], e[14]];
  }
  function sub(a, b) { return [a[0]-b[0], a[1]-b[1], a[2]-b[2]]; }
  function norm(v) {
    const m = Math.hypot(v[0], v[1], v[2]) || 1;
    return [v[0]/m, v[1]/m, v[2]/m];
  }
  function cross(a, b) {
    return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]];
  }

  const out = [];
  for (const cand of spec.candidates) {
    reset();
    applyRots(B.arm, cand.arm);
    applyRots(B.fore, cand.fore);
    applyRots(B.wrist, cand.hand);
    bones[B.arm].updateMatrixWorld(true);

    const wrist = P(B.wrist);
    const mid1 = P(B.middle1);
    const idx1 = P(B.index1);
    const pky1 = P(B.pinky1);
    const elbow = P(B.fore);
    const shoulder = P(B.arm);

    const dedos = norm(sub(mid1, wrist));
    let palma = norm(cross(sub(pky1, idx1), sub(mid1, wrist)));
    if (spec.flipPalma) palma = [-palma[0], -palma[1], -palma[2]];
    const antebrazo = norm(sub(wrist, elbow));
    const brazo = norm(sub(elbow, shoulder));
    out.push({ c: cand, dedos, palma, antebrazo, brazo, rel: sub(wrist, shoulder) });
  }
  return out;
}
"""


def dot(a, b):
    return sum(a[i] * b[i] for i in range(3))


def make_score(side):
    # La mano debe quedar delante del hombro y hacia el lado del cuerpo que le
    # toca, no cruzada sobre el pecho ni junto a la oreja.
    lateral = 1 if side == "left" else -1

    def score(m):
        s = 3.0 * dot(m["dedos"], [0, 1, 0])
        s += 3.0 * dot(m["palma"], [0, 0, 1])
        s += 1.2 * dot(m["antebrazo"], [0, 1, 0])
        s += 0.8 * dot(m["brazo"], [0, -1, 0])
        rx, ry, rz = m["rel"]
        s += 1.5 * max(0.0, min(rz / 0.30, 1.0))
        s -= 2.0 * max(0.0, ry - 0.05)
        s -= 1.5 * max(0.0, -lateral * rx + 0.02)
        return s

    return score


def run(page, spec_bones, candidates, score, flip, top=8):
    res = page.evaluate(
        SEARCH_JS,
        {"bones": spec_bones, "candidates": candidates, "flipPalma": flip},
    )
    res.sort(key=score, reverse=True)
    for m in res[:top]:
        print(
            f"  score={score(m):6.3f} arm={m['c'].get('arm')} fore={m['c'].get('fore')} "
            f"hand={m['c'].get('hand')}"
        )
        print(
            f"      dedos={lab.r3(m['dedos'])} palma={lab.r3(m['palma'])} "
            f"antebrazo={lab.r3(m['antebrazo'])} brazo={lab.r3(m['brazo'])} rel={lab.r3(m['rel'])}"
        )
    return res


def main():
    side = sys.argv[1] if len(sys.argv) > 1 else lab.SIDE
    b = lab.bones(side)
    spec_bones = {
        "arm": b["arm"],
        "fore": b["fore"],
        "wrist": b["wrist"],
        "index1": b["index"][0],
        "middle1": b["middle"][0],
        "pinky1": b["pinky"][0],
    }
    score = make_score(side)
    flip = side == "left"

    catalog = lab.load_catalog()
    catalog["rig"]["restCorrections"] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(args=lab.CHROME_ARGS)
        page = lab.open_lab(browser, catalog)

        print(f"== bind sin correcciones ({side}) ==")
        run(page, spec_bones, [{"arm": [], "fore": [], "hand": []}], score, flip, top=1)

        print("\n== etapa 1: brazo + antebrazo ==")
        cands = []
        for az in range(-180, 181, 15):
            for ax in range(-180, 181, 30):
                for ay in range(-60, 61, 30):
                    for fx in range(-180, 181, 30):
                        cands.append(
                            {"arm": [["z", az], ["x", ax], ["y", ay]], "fore": [["x", fx]]}
                        )
        stage1 = run(page, spec_bones, cands, score, flip, top=5)
        best = stage1[0]["c"]

        print("\n== etapa 2: mano ==")
        cands = []
        for hx in range(-180, 181, 15):
            for hy in range(-180, 181, 15):
                for hz in range(-180, 181, 15):
                    cands.append(
                        {
                            "arm": best["arm"],
                            "fore": best["fore"],
                            "hand": [["x", hx], ["y", hy], ["z", hz]],
                        }
                    )
        stage2 = run(page, spec_bones, cands, score, flip, top=5)

        # Entre empates, la correccion mas simple (menos grados) es la mejor.
        top_score = score(stage2[0])
        finalists = [m for m in stage2 if score(m) > top_score - 1e-6]
        finalists.sort(key=lambda m: sum(abs(r[1]) for r in m["c"]["hand"]))
        print("\nMEJOR:", json.dumps(finalists[0]["c"], ensure_ascii=False))
        browser.close()


if __name__ == "__main__":
    main()
