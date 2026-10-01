"""Busqueda final de la E.

Anade a search_e9 la medida que de verdad importa: la separacion de los dedos
TAL COMO SE VEN desde la camara de la app. Dos dedos pueden estar separados en
3D y aun asi solaparse en pantalla, que es lo que hace que la letra se lea como
un bulto en vez de como cuatro dedos.
"""
import itertools
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from pose_lab_e import _GET_SCENE
from search_e9 import MEASURE_JS, abrir, banda, pose_e

ROOT = Path(__file__).resolve().parents[1]

# Camara de produccion (rig.cameraTarget / rig.cameraOrbit del catalogo).
CAM_PROD_JS = """
() => {
  const mv = document.getElementById('handViewer');
  mv.minCameraOrbit = 'auto 0deg 0.05m';
  mv.maxCameraOrbit = 'auto 180deg 10m';
  mv.minFieldOfView = '2deg';
  mv.cameraTarget = '0m 2.45m 0.15m';
  mv.cameraOrbit = '0deg 84deg 2.5m';
  mv.fieldOfView = '30deg';
  mv.jumpCameraToGoal();
}
"""

# Separacion 2D entre dedos vecinos en la imagen, normalizada al largo de la
# palma proyectado. Se compara segmento contra segmento, no solo las yemas.
SCREEN_JS = (
    """
() => {
  const mv = document.getElementById('handViewer');
"""
    + _GET_SCENE
    + """
  const scene = getScene(mv);
  if (!scene) return { error: 'no-scene' };
  const cam = scene.camera || (scene.getCamera && scene.getCamera());
  if (!cam) return { error: 'no-camera' };
  scene.updateMatrixWorld(true);
  cam.updateMatrixWorld(true);
  const B = {};
  scene.traverse((o) => { if (o && o.name) B[o.name] = o; });

  const m = cam.projectionMatrix.elements, v = cam.matrixWorldInverse.elements;
  const mvp = new Array(16);
  for (let i = 0; i < 4; i++) for (let j = 0; j < 4; j++) {
    let s = 0;
    for (let k = 0; k < 4; k++) s += m[k * 4 + j] * v[i * 4 + k];
    mvp[i * 4 + j] = s;
  }
  function proj(n) {
    const b = B[n];
    if (!b) return null;
    const e = b.matrixWorld.elements;
    const x = e[12], y = e[13], z = e[14];
    const w = mvp[3]*x + mvp[7]*y + mvp[11]*z + mvp[15];
    if (!w) return null;
    return {
      x: (mvp[0]*x + mvp[4]*y + mvp[8]*z + mvp[12]) / w,
      y: (mvp[1]*x + mvp[5]*y + mvp[9]*z + mvp[13]) / w,
    };
  }
  const cad = {
    I: ['Index1_040','Index2_041','Index3_042','Index4_043'],
    M: ['Middle1_044','Middle2_045','Middle3_046','Middle4_047'],
    R: ['Ring1_048','Ring2_049','Ring3_050','Ring4_051'],
    P: ['Pinky1_052','Pinky2_053','Pinky3_054','Pinky4_055'],
  };
  const pts = {};
  Object.keys(cad).forEach((k) => {
    pts[k] = cad[k].map((s) => proj('mixamorig1RightHand' + s)).filter(Boolean);
  });
  const wrist = proj('mixamorig1RightHand_035');
  const knuI = proj('mixamorig1RightHandIndex1_040');
  const palm = Math.hypot(wrist.x-knuI.x, wrist.y-knuI.y) || 1;

  function segDist(p, a, b) {
    const abx = b.x-a.x, aby = b.y-a.y;
    const l2 = abx*abx + aby*aby || 1;
    let t = ((p.x-a.x)*abx + (p.y-a.y)*aby) / l2;
    t = Math.max(0, Math.min(1, t));
    return Math.hypot(p.x - (a.x+abx*t), p.y - (a.y+aby*t));
  }
  function polyDist(A, B2) {
    let best = Infinity;
    // solo desde la falange media hacia la yema: en la base los dedos se
    // tocan siempre y eso no es un defecto
    for (let i = 1; i < A.length; i++) {
      for (let j = 1; j < B2.length; j++) {
        best = Math.min(best, segDist(A[i], B2[j-1], B2[j]), segDist(B2[j], A[i-1], A[i]));
      }
    }
    return best;
  }
  const o = {};
  o.scrIM = polyDist(pts.I, pts.M) / palm;
  o.scrMR = polyDist(pts.M, pts.R) / palm;
  o.scrRP = polyDist(pts.R, pts.P) / palm;
  o.scrMin = Math.min(o.scrIM, o.scrMR, o.scrRP);
  // los nudillos marcan el techo alcanzable en esta proyeccion
  const k = ['Index1_040','Middle1_044','Ring1_048','Pinky1_052'].map((s) => proj('mixamorig1RightHand' + s));
  o.scrKnu = Math.min(
    Math.hypot(k[0].x-k[1].x, k[0].y-k[1].y),
    Math.hypot(k[1].x-k[2].x, k[1].y-k[2].y),
    Math.hypot(k[2].x-k[3].x, k[2].y-k[3].y)
  ) / palm;
  // altura de la yema respecto al nudillo en pantalla (la E baja las yemas)
  const tips = ['Index4_043','Middle4_047','Ring4_051','Pinky4_055'].map((s) => proj('mixamorig1RightHand' + s));
  let foldMin = 9;
  for (let i = 0; i < 4; i++) foldMin = Math.min(foldMin, (tips[i].y - k[i].y) / palm);
  o.scrFold = foldMin;  // eje y de NDC va hacia arriba: negativo = yema debajo
  return o;
}
"""
)


def puntuar(m, s):
    """m = metricas 3D, s = metricas de pantalla. Menor es mejor."""
    p = 0.0
    # 1) que no se peguen ni en 3D ni en la imagen
    p += 5.0 * banda(m["sepMin"], 0.17, 0.26)
    p += 8.0 * banda(s["scrMin"], 0.13, 0.40)
    # 2) dedos doblados: la yema por debajo del nudillo tambien en pantalla
    p += 3.0 * banda(-s["scrFold"], 0.28, 0.90)
    p += 2.0 * banda(m["foldMin"], 0.30, 1.10)
    p += 1.5 * banda(m["frontMin"], 0.10, 0.80)
    # 3) pulgar corto, del lado del indice, por delante y bajo las yemas
    p += 5.0 * banda(m["across"], 0.15, 0.45)
    p += 3.0 * banda(m["thumbLen"], 0.18, 0.40)
    p += 2.0 * banda(m["tipoI"], 0.10, 0.40)
    p += 1.5 * banda(m["thumbFront"], 0.15, 0.75)
    p += 1.5 * banda(m["thumbUnderTips"], -0.05, 0.55)
    return p


def linea(nombre, m, s, score):
    return (
        f"{nombre:38s} sc={score:6.3f} sep3d={m['sepMin']:.3f} scr={s['scrMin']:.3f} "
        f"fold={-s['scrFold']:+.2f} across={m['across']:+.2f} "
        f"tLen={m['thumbLen']:.2f} tipoI={m['tipoI']:.2f}"
    )


def main():
    cat = json.loads((ROOT / "data" / "catalogo-lsm.json").read_text("utf-8"))
    actual = next(x for x in cat["senas"] if x["letra"] == "E")["pose"]

    with sync_playwright() as p:
        browser, page = abrir(p)
        page.evaluate(CAM_PROD_JS)
        time.sleep(0.5)

        def ev(pose):
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
            return page.evaluate(MEASURE_JS), page.evaluate(SCREEN_JS)

        m0, s0 = ev(actual)
        print("ACTUAL:", linea("E_catalogo", m0, s0, puntuar(m0, s0)))
        print(f"        techo en pantalla (nudillos) = {s0['scrKnu']:.3f}\n")

        th0 = dict(tcurl=0.6, taside=-0.5, t1y=-60, t1z=10, t2x=60, t3x=0)
        g1 = list(
            itertools.product(
                (55, 70, 85, 100),        # mcp
                (85, 100, 115),           # pip
                (0, 20, 40),              # dip
                (-4, 0, 4, 8),            # conv
            )
        )
        print(f"Fase 1 (dedos): {len(g1)}")
        r1 = []
        for mcp, pip, dip, conv in g1:
            m, s = ev(pose_e(mcp, pip, dip, conv, **th0))
            sc = (
                5.0 * banda(m["sepMin"], 0.17, 0.26)
                + 8.0 * banda(s["scrMin"], 0.13, 0.40)
                + 3.0 * banda(-s["scrFold"], 0.28, 0.90)
                + 2.0 * banda(m["foldMin"], 0.30, 1.10)
                + 1.5 * banda(m["frontMin"], 0.10, 0.80)
            )
            r1.append((sc, (mcp, pip, dip, conv), m, s))
        r1.sort(key=lambda t: t[0])
        for sc, k, m, s in r1[:10]:
            print(" ", linea(f"mcp{k[0]} pip{k[1]} dip{k[2]} conv{k[3]}", m, s, sc))
        print()

        g2 = list(
            itertools.product(
                (0.5, 0.7, 0.9),          # tcurl
                (-45, -60, -75),          # t1y
                (0, 15, 30),              # t1z
                (60, 80, 100),            # t2x
                (30, 50, 70),             # t3x
            )
        )
        top_dedos = [k for _, k, _, _ in r1[:4]]
        print(f"Fase 2 (pulgar): {len(g2)} x {len(top_dedos)}")
        r2 = []
        for dedos in top_dedos:
            mcp, pip, dip, conv = dedos
            for tcurl, t1y, t1z, t2x, t3x in g2:
                m, s = ev(
                    pose_e(mcp, pip, dip, conv, tcurl, -0.5, t1y, t1z, t2x, t3x)
                )
                r2.append(
                    (puntuar(m, s), (dedos, (tcurl, t1y, t1z, t2x, t3x)), m, s)
                )
        r2.sort(key=lambda t: t[0])
        print("MEJORES")
        for sc, k, m, s in r2[:15]:
            d, t = k
            print(
                " ",
                linea(
                    f"mcp{d[0]} pip{d[1]} dip{d[2]} c{d[3]}|tc{t[0]} y{t[1]} z{t[2]} t2{t[3]} t3{t[4]}",
                    m, s, sc,
                ),
            )
        browser.close()

    out = ROOT / "tools" / "screenshots" / "search_e10.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(
            [
                {"score": sc, "dedos": k[0], "pulgar": k[1], "m3d": m, "pantalla": s}
                for sc, k, m, s in r2[:40]
            ],
            indent=2,
        ),
        "utf-8",
    )
    print("\n->", out)


if __name__ == "__main__":
    main()
