"""La O de la foto: circulo de pulgar e indice, los otros tres dedos en la palma.

El catalogo tenia los cuatro dedos en el mismo arco (se lee como una C). Aqui se
busca el cierre de la imagen: la yema del indice toca la del pulgar y deja un
agujero redondo, y medio, anular y menique quedan doblados dentro del puno.
"""
import itertools
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

import search_e9

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "o_circulo"
CATALOGO = ROOT / "data" / "catalogo-lsm.json"

search_e9.URL = "http://127.0.0.1:8124/practica.html?letra=O&v=ocirculo"

# Giro que ya deja la mano en la orientacion de la seña (ver muneca_natural).
MANO = {"x": -28.933, "y": -3.319, "z": -10.592}

MEDIR_JS = r"""
(pose) => {
  const c = window.__LSM_CONTROLLER__;
  c.applyTestPose(pose);
  const mv = document.getElementById('handViewer');
  let scene = null;
  for (const sym of Object.getOwnPropertySymbols(mv)) {
    const v = mv[sym];
    if (v && typeof v.traverse === 'function') { scene = v; break; }
    if (v && v.model && typeof v.model.traverse === 'function') { scene = v.model; break; }
    if (v && v.target && typeof v.target.traverse === 'function') { scene = v.target; break; }
  }
  if (!scene) return { error: 'no-scene' };
  scene.updateMatrixWorld(true);
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
  const grados = (u, v) => Math.acos(Math.max(-1, Math.min(1, dot(u, v) / ((len(u)||1)*(len(v)||1))))) * 180 / Math.PI;

  const wrist = P('RightHand');
  const knuI = P('RightHandIndex1');
  if (!wrist || !knuI) return { error: 'faltan-huesos', tiene: Object.keys(B).filter(n => n.indexOf('RightHand')===0).slice(0, 8) };
  const palm = dist(wrist, knuI) || 1;
  const nombres = ['Thumb1','Thumb2','Thumb3','Thumb4','Index1','Index2','Index3','Index4',
    'Middle1','Middle4','Ring1','Ring4','Pinky1','Pinky4','Middle2','Middle3','Ring2','Ring3','Pinky2','Pinky3'];
  const pt = {};
  for (const n of nombres) {
    pt[n] = P('RightHand' + n);
    if (!pt[n]) return { error: 'falta-' + n };
  }
  const aro = ['Thumb1','Thumb2','Thumb3','Thumb4','Index4','Index3','Index2','Index1'].map(n => pt[n]);
  const centro = mul(aro.reduce(add, {x:0,y:0,z:0}), 1/aro.length);
  const radios = aro.map(p => dist(p, centro) / palm);
  const radio = radios.reduce((a,b)=>a+b,0) / radios.length;
  const redondez = (Math.max(...radios) - Math.min(...radios)) / (radio || 1);
  const aSeg = (p, a, b) => {
    const ab = sub(b, a);
    const l2 = dot(ab, ab) || 1;
    const t = Math.max(0, Math.min(1, dot(sub(p, a), ab) / l2));
    return dist(p, add(a, mul(ab, t)));
  };
  const pinza = Math.min(aSeg(pt.Index4, pt.Thumb3, pt.Thumb4), aSeg(pt.Thumb4, pt.Index3, pt.Index4)) / palm;
  const cierre = dist(pt.Thumb4, pt.Index4) / palm;
  const ang = (a, b, c) => grados(sub(b, a), sub(c, b));
  const dedo = (k, a, m, t) => ({
    pip: ang(pt[k], pt[a], pt[m]),
    dip: ang(pt[a], pt[m], pt[t]),
    bajo: dist(pt[t], wrist) / palm,
  });
  const I = dedo('Index1','Index2','Index3','Index4');
  const M = dedo('Middle1','Middle2','Middle3','Middle4');
  const R = dedo('Ring1','Ring2','Ring3','Ring4');
  const K = dedo('Pinky1','Pinky2','Pinky3','Pinky4');
  // el medio no debe meterse en el agujero
  const medioCentro = dist(pt.Middle4, centro) / palm;
  return {
    palm, pinza, cierre, radio, redondez, medioCentro,
    ipip: I.pip, idip: I.dip, ibajo: I.bajo,
    mpip: M.pip, mdip: M.dip, mbajo: M.bajo,
    rpip: R.pip, ppip: K.pip,
    gapIM: dist(pt.Index4, pt.Middle4) / palm,
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
    p += 8.0 * banda(m["pinza"], 0.0, 0.07)
    p += 4.0 * banda(m["cierre"], 0.0, 0.12)
    p += 3.0 * banda(m["radio"], 0.15, 0.28)
    p += 3.0 * banda(m["redondez"], 0.0, 0.38)
    # indice curvado, no un puno ni un dedo recto
    p += 2.0 * banda(m["ipip"], 48, 88)
    p += 1.2 * banda(m["idip"], 20, 55)
    # los otros tres bien cerrados
    p += 2.5 * banda(m["mpip"], 78, 115)
    p += 1.5 * banda(m["rpip"], 78, 115)
    p += 1.5 * banda(m["ppip"], 75, 115)
    # el medio queda mas cerca de la muneca que el indice (esta en la palma)
    if m["mbajo"] > m["ibajo"] - 0.05:
        p += 2.0 * (m["mbajo"] - (m["ibajo"] - 0.05))
    # y no se mete en el aro
    if m["medioCentro"] < m["radio"] * 1.15:
        p += 3.0 * (m["radio"] * 1.15 - m["medioCentro"])
    return p


def pose(icurl, i1, i2, i3, ispread, tcurl, aside, t1x, t1y, t1z, t2x, t3x, muneca, cerrar=0.94):
    extra = {
        "RightHand": dict(MANO),
        "RightHandMiddle1": {"x": 12},
        "RightHandRing1": {"x": 12},
        "RightHandPinky1": {"x": 12},
    }
    if i1:
        extra["RightHandIndex1"] = {"x": i1}
    if i2:
        extra["RightHandIndex2"] = {"x": i2}
    if i3:
        extra["RightHandIndex3"] = {"x": i3}
    t1 = {}
    if t1x:
        t1["x"] = t1x
    if t1y:
        t1["y"] = t1y
    if t1z:
        t1["z"] = t1z
    if t1:
        extra["RightHandThumb1"] = t1
    if t2x:
        extra["RightHandThumb2"] = {"x": t2x}
    if t3x:
        extra["RightHandThumb3"] = {"x": t3x}
    out = {
        "thumb": {"curl": tcurl, "aside": aside},
        "index": {"curl": icurl, "spread": ispread},
        "middle": {"curl": cerrar},
        "ring": {"curl": cerrar},
        "pinky": {"curl": cerrar},
        "extra": extra,
    }
    if muneca:
        out["muneca"] = dict(muneca)
    return out


def evaluar_lote(page, poses):
    return page.evaluate(
        """(arg) => {
            const fn = eval(arg.js);
            const out = [];
            for (const pose of arg.poses) out.push(fn(pose));
            return out;
        }""",
        {"js": MEDIR_JS, "poses": poses},
    )


def linea(nombre, m, s):
    if m.get("error"):
        return f"{nombre}: {m['error']}"
    return (
        f"{nombre:22s} score={s:6.3f} pinza={m['pinza']:.3f} cierre={m['cierre']:.3f} "
        f"radio={m['radio']:.3f} red={m['redondez']:.2f} "
        f"I={m['ipip']:.0f}/{m['idip']:.0f} M={m['mpip']:.0f} "
        f"bajo I/M={m['ibajo']:.2f}/{m['mbajo']:.2f} gap={m['gapIM']:.2f}"
    )


def buscar(page):
    # pulgar de partida parecido al que ya cerraba contra el arco
    base_t = dict(tcurl=0.55, aside=-0.35, t1x=-10, t1y=20, t1z=30, t2x=30, t3x=35)
    rejilla = []
    for icurl, i1, i3, ispread in itertools.product(
        (0.42, 0.55, 0.68),
        (0, 16, 32),
        (-18, 0, 16),
        (0, 10),
    ):
        rejilla.append(pose(icurl, i1, 0, i3, ispread, muneca={"y": 25}, **base_t))
    print(f"fase indice: {len(rejilla)}")
    medidas = evaluar_lote(page, rejilla)
    rank = sorted(zip(rejilla, medidas), key=lambda it: puntuar(it[1]))
    print("mejores indices:")
    for pz, m in rank[:6]:
        print(" ", linea(
            f"c{pz['index']['curl']}_i1{pz['extra'].get('RightHandIndex1',{}).get('x',0)}"
            f"_i3{pz['extra'].get('RightHandIndex3',{}).get('x',0)}_s{pz['index']['spread']}",
            m, puntuar(m),
        ))
    mejor_i = rank[0][0]
    pulgares = []
    for tcurl, aside, t1y, t1z, t2x, t3x in itertools.product(
        (0.30, 0.48, 0.66, 0.82),
        (-0.7, -0.3, 0.05, 0.4),
        (-30, 10, 45),
        (0, 35, 65),
        (10, 35, 55),
        (10, 35, 55),
    ):
        pulgares.append(pose(
            mejor_i["index"]["curl"],
            mejor_i["extra"].get("RightHandIndex1", {}).get("x", 0),
            0,
            mejor_i["extra"].get("RightHandIndex3", {}).get("x", 0),
            mejor_i["index"]["spread"],
            tcurl, aside, -10, t1y, t1z, t2x, t3x,
            {"y": 25},
        ))
    print(f"fase pulgar: {len(pulgares)}")
    med_p = evaluar_lote(page, pulgares)
    rank_p = sorted(zip(pulgares, med_p), key=lambda it: puntuar(it[1]))
    print("mejores pulgares:")
    for pz, m in rank_p[:8]:
        t = pz["thumb"]
        e = pz["extra"]
        print(" ", linea(
            f"tc{t['curl']}_a{t['aside']}_y{e.get('RightHandThumb1',{}).get('y',0)}"
            f"_z{e.get('RightHandThumb1',{}).get('z',0)}"
            f"_t2{e.get('RightHandThumb2',{}).get('x',0)}"
            f"_t3{e.get('RightHandThumb3',{}).get('x',0)}",
            m, puntuar(m),
        ))
    return rank_p[:6]


def encuadrar(page, orbit, fov, target):
    for _ in range(2):
        page.evaluate(
            """(a) => {
                const mv = document.getElementById('handViewer');
                mv.minCameraOrbit = 'auto 0deg 0.05m';
                mv.maxCameraOrbit = 'auto 180deg 10m';
                mv.minFieldOfView = '2deg';
                mv.cameraTarget = a.t;
                mv.cameraOrbit = a.o;
                mv.fieldOfView = a.f;
                mv.jumpCameraToGoal();
            }""",
            {"t": target, "o": orbit, "f": fov},
        )
        time.sleep(0.25)


def retratar(page, casos):
    OUT.mkdir(parents=True, exist_ok=True)
    viewer = page.query_selector("#handViewer")
    for nombre, pz in casos:
        page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pz)
        time.sleep(0.25)
        m = page.evaluate(MEDIR_JS, pz)
        print(linea(nombre, m, puntuar(m)))
        hand = page.evaluate(
            """() => {
              const mv = document.getElementById('handViewer');
              let s = null;
              for (const sym of Object.getOwnPropertySymbols(mv)) {
                const v = mv[sym];
                if (v && typeof v.traverse === 'function') { s = v; break; }
              }
              s.updateMatrixWorld(true);
              const B = {};
              s.traverse((o) => { if (o && o.name) B[o.name] = o; });
              const e = B.RightHand.matrixWorld.elements;
              const off = (s.target && s.target.position) || { x: 0, y: 0, z: 0 };
              return { x: e[12] - off.x, y: e[13] - off.y, z: e[14] - off.z };
            }"""
        )
        t = "%.3fm %.3fm %.3fm" % (hand["x"], hand["y"], hand["z"])
        for vista, orbit, fov in (
            ("app", "0deg 78deg 0.52m", "30deg"),
            ("frente", "15deg 72deg 0.42m", "22deg"),
            ("lado", "-50deg 78deg 0.42m", "22deg"),
        ):
            encuadrar(page, orbit, fov, t)
            viewer.screenshot(path=str(OUT / f"{nombre}_{vista}.png"))


def main():
    cat = json.loads(CATALOGO.read_text(encoding="utf-8"))
    actual = next(s for s in cat["senas"] if s["letra"] == "O")["pose"]
    with sync_playwright() as p:
        browser, page = search_e9.abrir(p)
        page.set_default_timeout(180000)
        page.set_viewport_size({"width": 900, "height": 900})
        time.sleep(0.4)
        print("--- actual ---")
        m0 = page.evaluate(MEDIR_JS, actual)
        print(linea("catalogo", m0, puntuar(m0)))
        mejores = buscar(page)
        casos = [("00_catalogo", actual)]
        for i, (pz, _m) in enumerate(mejores[:3], start=1):
            # la misma forma, tres giros de muneca para ver el agujero de frente
            for giro, y in (("a", 0), ("b", 35), ("c", 70)):
                q = json.loads(json.dumps(pz))
                q["muneca"] = {"y": y}
                casos.append((f"{i:02d}{giro}", q))
        retratar(page, casos)
        (OUT / "_top.json").write_text(
            json.dumps([pz for pz, _ in mejores], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        browser.close()


if __name__ == "__main__":
    main()
