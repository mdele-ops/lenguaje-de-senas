"""Busqueda de la E con el reparto anatomico correcto.

El error de la version anterior: se flexiono el NUDILLO (MCP) 85 grados, lo que
saca el dedo entero por delante de la palma y deja una garra. En la E de la LSM
el nudillo casi no se dobla (el dedo sigue la linea de la palma) y el doblez va
en las dos articulaciones de arriba:

    MCP  15-40    el dedo sigue subiendo desde el nudillo
    PIP  85-110   aqui esta el codo del dedo, en lo alto de la mano
    DIP  50-85    la yema se curva hacia dentro y aterriza sobre el pulgar

Asi las yemas bajan pegadas a la palma y se apoyan en el pulgar, en vez de
quedar colgando delante de ella.
"""
import itertools
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from pose_lab_e import _GET_SCENE
from search_e9 import abrir, banda, pose_e

ROOT = Path(__file__).resolve().parents[1]

MEASURE_JS = (
    """
() => {
  const mv = document.getElementById('handViewer');
"""
    + _GET_SCENE
    + """
  const scene = getScene(mv);
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
  const dot = (a, b) => a.x*b.x + a.y*b.y + a.z*b.z;
  const len = (a) => Math.hypot(a.x, a.y, a.z);
  const norm = (a) => { const l = len(a) || 1; return { x: a.x/l, y: a.y/l, z: a.z/l }; };
  const cross = (a, b) => ({ x: a.y*b.z-a.z*b.y, y: a.z*b.x-a.x*b.z, z: a.x*b.y-a.y*b.x });
  const ang = (a, b) => Math.acos(Math.max(-1, Math.min(1, dot(norm(a), norm(b))))) * 180 / Math.PI;
  const dist = (a, b) => len(sub(a, b));
  function segClosest(p, a, b) {
    const ab = sub(b, a);
    const l2 = dot(ab, ab) || 1;
    let t = dot(sub(p, a), ab) / l2;
    t = Math.max(0, Math.min(1, t));
    return { x: a.x + ab.x*t, y: a.y + ab.y*t, z: a.z + ab.z*t };
  }

  const N = (s) => 'mixamorig1RightHand' + s;
  const wrist = P('mixamorig1RightHand_035');
  const cad = {
    I: ['Index1_040','Index2_041','Index3_042','Index4_043'],
    M: ['Middle1_044','Middle2_045','Middle3_046','Middle4_047'],
    R: ['Ring1_048','Ring2_049','Ring3_050','Ring4_051'],
    P: ['Pinky1_052','Pinky2_053','Pinky3_054','Pinky4_055'],
  };
  const J = {};
  Object.keys(cad).forEach((k) => { J[k] = cad[k].map((s) => P(N(s))); });

  const palmLen = dist(wrist, J.I[0]) || 1;
  // marco de la palma: largo, ancho y "frente" (cara palmar, hacia la camara)
  const largo = norm(sub(J.I[0], wrist));
  const ancho = norm(sub(J.P[0], J.I[0]));
  const frente = norm(cross(largo, ancho));

  const t2 = P(N('Thumb2_037')), t3 = P(N('Thumb3_038')), t4 = P(N('Thumb4_039'));

  const o = { palm: palmLen };
  const claves = ['I','M','R','P'];

  // angulos de flexion de cada articulacion
  let mcpMin = 999, mcpMax = -999, pipMin = 999, dipMin = 999;
  let fueraMax = -999;
  claves.forEach((k) => {
    const j = J[k];
    const prox = sub(j[1], j[0]), midd = sub(j[2], j[1]), dst = sub(j[3], j[2]);
    const mcp = ang(largo, prox), pip = ang(prox, midd), dip = ang(midd, dst);
    mcpMin = Math.min(mcpMin, mcp); mcpMax = Math.max(mcpMax, mcp);
    pipMin = Math.min(pipMin, pip); dipMin = Math.min(dipMin, dip);
    // cuanto se sale del plano de la palma la falange proximal: si es grande,
    // el dedo entero se va hacia delante y aparece la garra
    fueraMax = Math.max(fueraMax, Math.abs(90 - ang(frente, prox)));
  });
  o.mcp = mcpMin; o.mcpMax = mcpMax; o.pip = pipMin; o.dip = dipMin;
  o.proxFuera = fueraMax;

  // la yema apoyada en el pulgar y pegada a la palma (nada de garra)
  let yemaThumb = -999, yemaFrente = -999, yemaFrenteMin = 999;
  claves.forEach((k) => {
    const tip = J[k][3];
    yemaThumb = Math.max(yemaThumb, dist(tip, segClosest(tip, t2, t4)) / palmLen);
    const f = dot(sub(tip, J[k][0]), frente) / palmLen;
    yemaFrente = Math.max(yemaFrente, f);
    yemaFrenteMin = Math.min(yemaFrenteMin, f);
  });
  o.yemaThumb = yemaThumb;
  o.yemaFrente = yemaFrente;
  o.yemaFrenteMin = yemaFrenteMin;

  // la yema por debajo del nudillo (la E baja los dedos)
  let bajaMin = 999;
  claves.forEach((k) => {
    bajaMin = Math.min(bajaMin, dot(sub(J[k][0], J[k][3]), largo) / palmLen);
  });
  o.baja = bajaMin;

  // separacion entre dedos vecinos, en las tres articulaciones de arriba
  let sepMin = 999;
  for (let i = 0; i < 3; i++) {
    const a = J[claves[i]], b = J[claves[i+1]];
    for (let j = 1; j < 4; j++) sepMin = Math.min(sepMin, dist(a[j], b[j]) / palmLen);
  }
  o.sep = sepMin;
  o.sepNudillos = Math.min(
    dist(J.I[0], J.M[0]), dist(J.M[0], J.R[0]), dist(J.R[0], J.P[0])
  ) / palmLen;

  // pulgar: cuanto cruza (0 = indice, 1 = menique) y su largo visible
  const eje = sub(J.P[0], J.I[0]);
  const l2 = dot(eje, eje) || 1;
  o.across = dot(sub(t4, J.I[0]), eje) / l2;
  o.thumbLen = dist(t2, t4) / palmLen;
  o.thumbFrente = dot(sub(t4, J.I[0]), frente) / palmLen;
  o.t3 = dot(sub(t3, J.I[0]), eje) / l2;

  // Alturas a lo largo de la palma (0 = fila de nudillos, negativo = hacia la
  // muneca). Lo que distingue la E de la S: en la E el pulgar pasa por DEBAJO
  // de las yemas y estas se apoyan encima; en la S cruza por delante de ellas.
  const altura = (p) => dot(sub(p, J.I[0]), largo) / palmLen;
  let yemaAlturaMin = 999;
  claves.forEach((k) => { yemaAlturaMin = Math.min(yemaAlturaMin, altura(J[k][3])); });
  o.alturaYema = yemaAlturaMin;
  o.alturaPulgar = (altura(t3) + altura(t4)) / 2;
  o.pulgarBajoYemas = o.alturaYema - o.alturaPulgar;

  // En la foto de referencia el pulgar NO barre la palma: se dobla hacia
  // arriba por el lado del indice y su punta queda bajo la yema del indice.
  // pulgarArriba = 1 cuando apunta hacia los dedos, 0 cuando va atravesado.
  o.pulgarArriba = dot(norm(sub(t4, t2)), largo);
  o.tipoI = dist(t4, J.I[3]) / palmLen;
  o.tipoM = dist(t4, J.M[3]) / palmLen;
  return o;
}
"""
)


def puntuar(m):
    p = 0.0
    # reparto anatomico: el nudillo apenas se dobla, el doblez va arriba
    p += 6.0 * banda(m["mcp"], 15, 42)
    p += 4.0 * banda(m["pip"], 85, 112)
    p += 4.0 * banda(m["dip"], 50, 85)
    # el dedo no debe salirse del plano de la palma (eso es la garra)
    p += 5.0 * banda(m["proxFuera"], 0, 35)
    # yemas apoyadas en el pulgar, pegadas a la palma y por debajo del nudillo
    p += 5.0 * banda(m["yemaThumb"], 0.04, 0.22)
    p += 4.0 * banda(m["yemaFrente"], 0.10, 0.45)
    p += 3.0 * banda(m["baja"], 0.35, 1.00)
    # dedos separados (el arreglo anterior, que hay que conservar)
    p += 6.0 * banda(m["sep"], 0.17, 0.26)
    # pulgar corto y cruzado del lado del indice
    p += 5.0 * banda(m["across"], 0.15, 0.50)
    p += 3.0 * banda(m["thumbLen"], 0.18, 0.42)
    p += 2.0 * banda(m["thumbFrente"], 0.10, 0.45)
    return p


def linea(nombre, m, score):
    return (
        f"{nombre:36s} sc={score:6.3f} mcp={m['mcp']:5.1f} pip={m['pip']:5.1f} "
        f"dip={m['dip']:5.1f} fuera={m['proxFuera']:5.1f} | yema>pulgar={m['yemaThumb']:.2f} "
        f"frente={m['yemaFrente']:+.2f} baja={m['baja']:.2f} sep={m['sep']:.3f} "
        f"across={m['across']:+.2f}"
    )


def main():
    cat = json.loads((ROOT / "data" / "catalogo-lsm.json").read_text("utf-8"))
    actual = next(x for x in cat["senas"] if x["letra"] == "E")["pose"]

    with sync_playwright() as p:
        browser, page = abrir(p)

        def ev(pose):
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
            return page.evaluate(MEASURE_JS)

        m = ev(actual)
        print("ACTUAL (la garra):")
        print(" ", linea("E_catalogo", m, puntuar(m)))
        print(f"  nudillos separados {m['sepNudillos']:.3f}\n")

        th0 = dict(tcurl=0.9, taside=-0.5, t1y=-60, t1z=15, t2x=60, t3x=70)
        g1 = list(
            itertools.product(
                (0, 10, 20, 30),      # mcp extra
                (85, 95, 105),        # pip extra
                (40, 55, 70, 85),     # dip extra
                (-8, -4, 0),          # conv
            )
        )
        print(f"Fase 1 (reparto del doblez): {len(g1)}")
        r1 = []
        for mcp, pip, dip, conv in g1:
            mm = ev(pose_e(mcp, pip, dip, conv, **th0))
            sc = (
                6.0 * banda(mm["mcp"], 15, 42)
                + 4.0 * banda(mm["pip"], 85, 112)
                + 4.0 * banda(mm["dip"], 50, 85)
                + 5.0 * banda(mm["proxFuera"], 0, 35)
                + 4.0 * banda(mm["yemaFrente"], 0.10, 0.45)
                + 3.0 * banda(mm["baja"], 0.35, 1.00)
                + 6.0 * banda(mm["sep"], 0.17, 0.26)
            )
            r1.append((sc, (mcp, pip, dip, conv), mm))
        r1.sort(key=lambda t: t[0])
        for sc, k, mm in r1[:10]:
            print(" ", linea(f"mcp{k[0]} pip{k[1]} dip{k[2]} c{k[3]}", mm, sc))
        print()

        g2 = list(
            itertools.product(
                (0.5, 0.7, 0.9),          # tcurl
                (-40, -55, -70),          # t1y
                (0, 15, 30),              # t1z
                (40, 60, 80),             # t2x
                (30, 50, 70),             # t3x
            )
        )
        top = [k for _, k, _ in r1[:4]]
        print(f"Fase 2 (pulgar bajo las yemas): {len(g2)} x {len(top)}")
        r2 = []
        for dedos in top:
            mcp, pip, dip, conv = dedos
            for tcurl, t1y, t1z, t2x, t3x in g2:
                mm = ev(pose_e(mcp, pip, dip, conv, tcurl, -0.5, t1y, t1z, t2x, t3x))
                r2.append((puntuar(mm), (dedos, (tcurl, t1y, t1z, t2x, t3x)), mm))
        r2.sort(key=lambda t: t[0])
        print("MEJORES")
        for sc, k, mm in r2[:15]:
            d, t = k
            print(
                " ",
                linea(
                    f"m{d[0]} p{d[1]} d{d[2]} c{d[3]}|tc{t[0]} y{t[1]} z{t[2]} t2{t[3]} t3{t[4]}",
                    mm, sc,
                ),
            )
        browser.close()

    out = ROOT / "tools" / "screenshots" / "search_e11.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(
            [{"score": sc, "dedos": k[0], "pulgar": k[1], "m": mm} for sc, k, mm in r2[:40]],
            indent=2,
        ),
        "utf-8",
    )
    print("\n->", out)


if __name__ == "__main__":
    main()
