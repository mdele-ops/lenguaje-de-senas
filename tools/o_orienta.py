"""Gira la muneca de la O para que el agujero mire a la camara, como la foto.

La forma de los dedos no cambia: solo la orientacion. Se premia que el aro se
vea redondo y de frente, y que la muneca quede debajo, con la mano en vertical.
"""
import itertools
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

import search_e9

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "o_circulo" / "orienta"
CATALOGO = ROOT / "data" / "catalogo-lsm.json"
search_e9.URL = "http://127.0.0.1:8124/practica.html?letra=O&v=oorienta"

MEDIR = r"""
(pose) => {
  const c = window.__LSM_CONTROLLER__;
  c.applyTestPose(pose);
  const mv = document.getElementById('handViewer');
  let scene = null;
  for (const sym of Object.getOwnPropertySymbols(mv)) {
    const v = mv[sym];
    if (v && typeof v.traverse === 'function') { scene = v; break; }
  }
  if (!scene) return { error: 'no-scene' };
  scene.updateMatrixWorld(true);
  const cam = scene.camera || (scene.getCamera && scene.getCamera());
  if (cam && cam.updateMatrixWorld) cam.updateMatrixWorld(true);
  const B = {};
  scene.traverse((o) => { if (o && o.name) B[o.name] = o; });
  const P = (n) => {
    const b = B[n];
    if (!b) return null;
    const e = b.matrixWorld.elements;
    return { x: e[12], y: e[13], z: e[14] };
  };
  const sub = (a, b) => ({ x: a.x-b.x, y: a.y-b.y, z: a.z-b.z });
  const add = (a, b) => ({ x: a.x+b.x, y: a.y+b.y, z: a.z+b.z });
  const mul = (a, k) => ({ x: a.x*k, y: a.y*k, z: a.z*k });
  const dot = (a, b) => a.x*b.x + a.y*b.y + a.z*b.z;
  const len = (a) => Math.hypot(a.x, a.y, a.z);
  const dist = (a, b) => len(sub(a, b));
  const norm = (a) => { const l = len(a) || 1; return mul(a, 1/l); };
  const cross = (a, b) => ({ x: a.y*b.z-a.z*b.y, y: a.z*b.x-a.x*b.z, z: a.x*b.y-a.y*b.x });

  const wrist = P('RightHand');
  const pts = ['Thumb2','Thumb3','Thumb4','Index4','Index3','Index2'].map(n => P('RightHand'+n));
  if (!wrist || pts.some(p => !p) || !cam) return { error: 'faltan' };
  const centro = mul(pts.reduce(add, {x:0,y:0,z:0}), 1/pts.length);
  let sx=0, sy=0, sz=0, sxy=0, sxz=0, syz=0;
  pts.forEach(p => {
    const d = sub(p, centro);
    sx += d.x*d.x; sy += d.y*d.y; sz += d.z*d.z;
    sxy += d.x*d.y; sxz += d.x*d.z; syz += d.y*d.z;
  });
  let mejor = null;
  [{x:1,y:0,z:0},{x:0,y:1,z:0},{x:0,y:0,z:1},{x:1,y:1,z:1},{x:1,y:-1,z:0},{x:1,y:0,z:-1}].forEach(seed => {
    let v = norm(seed);
    for (let it = 0; it < 40; it++) {
      const tr = sx+sy+sz;
      v = norm({
        x: tr*v.x - (sx*v.x + sxy*v.y + sxz*v.z),
        y: tr*v.y - (sxy*v.x + sy*v.y + syz*v.z),
        z: tr*v.z - (sxz*v.x + syz*v.y + sz*v.z),
      });
    }
    const q = sx*v.x*v.x + sy*v.y*v.y + sz*v.z*v.z + 2*(sxy*v.x*v.y + sxz*v.x*v.z + syz*v.y*v.z);
    if (!mejor || q < mejor.q) mejor = { q, v };
  });
  const e = cam.matrixWorld.elements;
  const adelante = norm({ x: -e[8], y: -e[9], z: -e[10] });
  const frente = Math.abs(dot(mejor.v, adelante));

  const m = cam.projectionMatrix.elements, vi = cam.matrixWorldInverse.elements;
  const mvp = new Array(16);
  for (let i = 0; i < 4; i++) for (let j = 0; j < 4; j++) {
    let s = 0;
    for (let k = 0; k < 4; k++) s += m[k*4+j] * vi[i*4+k];
    mvp[i*4+j] = s;
  }
  const pr = (p) => {
    const w = mvp[3]*p.x + mvp[7]*p.y + mvp[11]*p.z + mvp[15];
    if (!w) return null;
    return {
      x: (mvp[0]*p.x + mvp[4]*p.y + mvp[8]*p.z + mvp[12]) / w,
      y: (mvp[1]*p.x + mvp[5]*p.y + mvp[9]*p.z + mvp[13]) / w,
    };
  };
  const sp = pts.map(pr), sw = pr(wrist);
  if (sp.some(p => !p) || !sw) return { error: 'proy' };
  const c2 = { x: sp.reduce((a,p)=>a+p.x,0)/sp.length, y: sp.reduce((a,p)=>a+p.y,0)/sp.length };
  const radios = sp.map(p => Math.hypot(p.x-c2.x, p.y-c2.y));
  const radio = radios.reduce((a,b)=>a+b,0) / radios.length;
  const red = (Math.max(...radios) - Math.min(...radios)) / (radio || 1);
  let area = 0;
  for (let i = 0; i < sp.length; i++) {
    const p = sp[i], q = sp[(i+1)%sp.length];
    area += p.x*q.y - q.x*p.y;
  }
  const knu = P('RightHandIndex1');
  const sk = pr(knu);
  return {
    frente, red, area: Math.abs(area),
    radio,
    munecaAbajo: c2.y - sw.y,
    vertical: sk ? (sk.y - sw.y) : 0,
  };
}
"""


def banda(v, lo, hi):
    if v < lo:
        return (lo - v) / (hi - lo or 1)
    if v > hi:
        return (v - hi) / (hi - lo or 1)
    return 0.0


def puntuar(m):
    if not m or m.get("error"):
        return 999.0
    p = 0.0
    p += 6.0 * (1.0 - min(m["frente"], 1.0))
    p += 4.0 * banda(m["red"], 0.0, 0.45)
    p += 3.0 * banda(m["area"], 0.012, 0.08)
    p += 3.0 * banda(m["munecaAbajo"], 0.04, 0.35)
    p += 2.0 * banda(m["vertical"], 0.02, 0.25)
    return p


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cat = json.loads(CATALOGO.read_text(encoding="utf-8"))
    base = next(s for s in cat["senas"] if s["letra"] == "O")["pose"]
    poses = []
    for x, y, z in itertools.product(
        (-30, 0, 30),
        (-90, -55, -20, 15, 50, 85),
        (-40, 0, 40),
    ):
        pz = json.loads(json.dumps(base))
        pz["muneca"] = {"x": x, "y": y, "z": z}
        poses.append(pz)
    with sync_playwright() as p:
        browser, page = search_e9.abrir(p)
        page.set_default_timeout(180000)
        page.set_viewport_size({"width": 720, "height": 720})
        viewer = page.query_selector("#handViewer")
        med = page.evaluate(
            """(arg) => {
              const fn = eval(arg.js);
              return arg.poses.map(fn);
            }""",
            {"js": MEDIR, "poses": poses},
        )
        rank = sorted(zip(poses, med), key=lambda it: puntuar(it[1]))
        print("top")
        for pz, m in rank[:8]:
            w = pz["muneca"]
            print(f"  x{w['x']} y{w['y']} z{w['z']}  {puntuar(m):6.3f}  {m}")
        for i, (pz, m) in enumerate(rank[:5], start=1):
            w = pz["muneca"]
            nombre = f"{i}_x{w['x']}_y{w['y']}_z{w['z']}"
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pz)
            time.sleep(0.35)
            viewer.screenshot(path=str(OUT / f"{nombre}.png"))
            (OUT / f"{nombre}.json").write_text(json.dumps(pz["muneca"]), encoding="utf-8")
            print("foto", nombre)
        browser.close()


if __name__ == "__main__":
    main()
