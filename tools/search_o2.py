"""O, paso 2: busqueda en rejilla del arco compacto + contacto con el pulgar.

La rejilla se recorre dentro del navegador (rapido) y despues se renderizan los
mejores candidatos para revisarlos a ojo contra la foto de referencia.
"""
import json

from playwright.sync_api import sync_playwright

import lsm_lab as L

OUT = L.out_dir("search_o2")

# Valores objetivo, leidos de la foto de referencia y normalizados al largo de
# la palma: indice y medio sobre el pulgar, anular y menique escalonados detras,
# y los cuatro dedos pegados entre si.
TARGET = {"dI": 0.05, "dM": 0.15, "dR": 0.30, "dP": 0.45}
WEIGHT = {"dI": 1.0, "dM": 0.7, "dR": 0.4, "dP": 0.25}
GAP_WEIGHT = 0.5

SEARCH_JS = r"""
(grid) => {
  const mv = document.getElementById('handViewer');
  const ctrl = window.__LSM_CONTROLLER__;
  """ + L._GET_SCENE + r"""
  const scene = getScene(mv);
  if (!scene) return { error: 'no-scene' };
  const bones = {};
  scene.traverse((o) => { if (o && o.name) bones[o.name] = o; });

  const ARM = 'mixamorig1RightArm_033';
  const T1 = 'mixamorig1RightHandThumb1_036';
  const T2 = 'mixamorig1RightHandThumb2_037';
  const F = grid.fingerBones;
  const NAMES = ['index','middle','ring','pinky'];

  function pos(n) {
    const b = bones[n];
    if (!b || !b.matrixWorld) return null;
    const e = b.matrixWorld.elements;
    return { x: e[12], y: e[13], z: e[14] };
  }
  function dist(a, b) { return (a && b) ? Math.hypot(a.x-b.x, a.y-b.y, a.z-b.z) : null; }

  function measure() {
    if (scene.updateMatrixWorld) scene.updateMatrixWorld(true);
    const t4 = pos('mixamorig1RightHandThumb4_039');
    const tip = NAMES.map((f) => pos(F[f][3]));
    const palm = dist(pos('mixamorig1RightHand_035'), pos(F.index[0])) || 1;
    return {
      dI: dist(t4, tip[0])/palm, dM: dist(t4, tip[1])/palm,
      dR: dist(t4, tip[2])/palm, dP: dist(t4, tip[3])/palm,
      gIM: dist(tip[0], tip[1])/palm,
      gMR: dist(tip[1], tip[2])/palm,
      gRP: dist(tip[2], tip[3])/palm,
    };
  }

  function buildPose(p) {
    const extra = { [ARM]: { z: -18 } };
    const fan = [-1.5, -0.5, 0.5, 1.5];
    const pose = {
      thumb: { curl: p.tcurl, aside: p.taside },
      muneca: { y: grid.wy },
    };
    NAMES.forEach((f, i) => {
      const b = F[f];
      extra[b[0]] = { x: p.k };
      if (p.m2) extra[b[1]] = { x: p.m2 };
      if (p.d3) extra[b[2]] = { x: p.d3 };
      pose[f] = { curl: p.c, spread: fan[i] * p.conv };
    });
    extra[T1] = { y: 0, z: p.t1z };
    extra[T2] = { x: p.t2x };
    pose.extra = extra;
    return pose;
  }

  const results = [];
  for (const conv of grid.conv)
  for (const c of grid.c)
  for (const k of grid.k)
  for (const m2 of grid.m2)
  for (const d3 of grid.d3)
  for (const tcurl of grid.tcurl)
  for (const taside of grid.taside)
  for (const t1z of grid.t1z)
  for (const t2x of grid.t2x) {
    const p = { conv, c, k, m2, d3, tcurl, taside, t1z, t2x };
    ctrl.applyTestPose(buildPose(p));
    const m = measure();
    results.push({ p: p, m: m });
  }
  return { count: results.length, results: results };
}
"""

GRID = {
    "fingerBones": L.FINGER_BONES,
    "wy": 50,
    "conv": [-20, -14, -8],
    "c": [0.44, 0.50, 0.56],
    "k": [8, 16, 24],
    "m2": [0, 12, 24],
    "d3": [0, -16, -32],
    "tcurl": [0.40, 0.48, 0.56],
    "taside": [0.20, 0.36, 0.52],
    "t1z": [22, 30, 38],
    "t2x": [-20, -28, -36],
}


def score(m):
    s = sum(WEIGHT[k] * abs(m[k] - TARGET[k]) for k in TARGET)
    s += GAP_WEIGHT * (m["gIM"] + m["gMR"] + m["gRP"])
    return s


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", args=L.CHROME_ARGS)
        page = L.open_ready_page(browser)

        out = page.evaluate(SEARCH_JS, GRID)
        if out.get("error"):
            raise RuntimeError(out["error"])
        res = out["results"]
        print("combinaciones evaluadas:", out["count"])

        for r in res:
            r["score"] = score(r["m"])
        res.sort(key=lambda r: r["score"])

        print("\n== top 12 ==")
        for r in res[:12]:
            m = r["m"]
            print(
                f"s={r['score']:.3f} dI={m['dI']:.2f} dM={m['dM']:.2f} "
                f"dR={m['dR']:.2f} dP={m['dP']:.2f} "
                f"g={m['gIM']:.2f}/{m['gMR']:.2f}/{m['gRP']:.2f}  {r['p']}"
            )

        (OUT / "ranking.json").write_text(
            json.dumps(res[:80], indent=2), encoding="utf-8"
        )

        # Render de los mejores para revisarlos a ojo
        viewer = page.query_selector("#viewer")
        for i, r in enumerate(res[:8]):
            pr = r["p"]
            fan = [-1.5, -0.5, 0.5, 1.5]
            pose = L.build_pose(
                curl=(pr["c"],) * 4,
                spread=tuple(f * pr["conv"] for f in fan),
                mcp=(pr["k"],) * 4,
                pip=(pr["m2"],) * 4,
                dip=(pr["d3"],) * 4,
                tcurl=pr["tcurl"],
                taside=pr["taside"],
                t1=(0, pr["t1z"]),
                t2x=pr["t2x"],
                wrist={"y": GRID["wy"]},
            )
            L.apply_pose(page, pose)
            L.set_camera(page, orbit="-40deg 82deg 0.40m", fov="24deg")
            viewer.screenshot(path=str(OUT / f"top{i:02d}_s{r['score']:.3f}.png"))

        browser.close()
        print("->", OUT)


if __name__ == "__main__":
    main()
