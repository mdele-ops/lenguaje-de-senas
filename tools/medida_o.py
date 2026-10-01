"""Medidas de la letra O: el anillo que forman pulgar e indice.

La O no se juzga como la E. En la E lo que importa es que los cuatro dedos
cierren igual; aqui lo que hace legible la letra es el AGUJERO: un aro redondo,
cerrado, y lo bastante grande para que se vea desde la camara de la app.

El aro se recorre por los ocho puntos de la cadena pulgar->indice
(T1 T2 T3 T4 - I4 I3 I2 I1) y se mide:

    cierre    hueco entre la punta del pulgar y la del indice. Es el unico
              tramo del aro que no lo dibuja un hueso, asi que si se abre el
              aro deja de leerse como O y pasa a leerse como C.
    radio     tamano del agujero (media de las distancias al centro), en
              largos de palma. Muy pequeno = punos; muy grande = C.
    redondez  dispersion de esos radios partida por la media. 0 = circulo
              perfecto; por encima de ~0.30 el agujero se ve como una gota.
    plano     cuanto se sale el aro de su propio plano. Si es alto el aro esta
              retorcido y desde la camara se ve como una raya, no como un
              agujero.

Todas las distancias van normalizadas al largo de la palma (muneca -> nudillo
del indice) para poder compararlas con la lamina de referencia.
"""
import json

import numpy as np

from pose_lab_e import _GET_SCENE

ARO = [
    "Thumb1_036", "Thumb2_037", "Thumb3_038", "Thumb4_039",
    "Index4_043", "Index3_042", "Index2_041", "Index1_040",
]

MEDIDA_O_JS = (
    """
() => {
  const mv = document.getElementById('handViewer');
"""
    + _GET_SCENE
    + """
  const scene = getScene(mv);
  if (!scene) return { error: 'no-scene' };
  scene.updateMatrixWorld(true);
  const cam = scene.camera || (scene.getCamera && scene.getCamera());
  if (cam) cam.updateMatrixWorld(true);
  const B = {};
  scene.traverse((o) => { if (o && o.name) B[o.name] = o; });
  const P = (n) => {
    const b = B['mixamorig1RightHand' + n];
    if (!b) return null;
    const e = b.matrixWorld.elements;
    return { x: e[12], y: e[13], z: e[14] };
  };
  const sub = (a, b) => ({ x: a.x-b.x, y: a.y-b.y, z: a.z-b.z });
  const add = (a, b) => ({ x: a.x+b.x, y: a.y+b.y, z: a.z+b.z });
  const mul = (a, k) => ({ x: a.x*k, y: a.y*k, z: a.z*k });
  const dot = (a, b) => a.x*b.x + a.y*b.y + a.z*b.z;
  const cross = (a, b) => ({ x: a.y*b.z-a.z*b.y, y: a.z*b.x-a.x*b.z, z: a.x*b.y-a.y*b.x });
  const len = (a) => Math.hypot(a.x, a.y, a.z);
  const norm = (a) => { const l = len(a) || 1; return mul(a, 1/l); };
  const dist = (a, b) => len(sub(a, b));
  const grados = (u, v) =>
    Math.acos(Math.max(-1, Math.min(1, dot(norm(u), norm(v))))) * 180 / Math.PI;
  const media = (v) => v.reduce((a, b) => a + b, 0) / (v.length || 1);
  const disp = (v) => Math.max.apply(null, v) - Math.min.apply(null, v);
  // distancia de un punto al segmento a-b (la yema toca el CUERPO del pulgar,
  // no siempre su punta)
  const aSeg = (p, a, b) => {
    const ab = sub(b, a);
    const l2 = dot(ab, ab) || 1;
    const t = Math.max(0, Math.min(1, dot(sub(p, a), ab) / l2));
    return dist(p, add(a, mul(ab, t)));
  };

  const wrist = P('_035');
  const knuI = P('Index1_040'), knuP = P('Pinky1_052');
  const palm = dist(wrist, knuI) || 1;
  const largo = norm(sub(knuI, wrist));
  const anchoV = sub(knuP, knuI);
  const ancho = norm(anchoV);
  const frente = norm(cross(largo, ancho));

  const o = { palm: palm };

  // ---- el aro ---------------------------------------------------------
  const aro = """
    + json.dumps(ARO)
    + """.map(P);
  if (aro.some((p) => !p)) return { error: 'faltan-huesos' };
  const centro = mul(aro.reduce(add, { x: 0, y: 0, z: 0 }), 1 / aro.length);
  const radios = aro.map((p) => dist(p, centro) / palm);
  o.radio = media(radios);
  o.redondez = disp(radios) / (o.radio || 1);

  // plano del aro por covarianza: la normal es el eje de menor varianza
  let sxx=0, syy=0, szz=0, sxy=0, sxz=0, syz=0;
  aro.forEach((p) => {
    const d = sub(p, centro);
    sxx += d.x*d.x; syy += d.y*d.y; szz += d.z*d.z;
    sxy += d.x*d.y; sxz += d.x*d.z; syz += d.y*d.z;
  });
  // iteracion inversa barata: se prueban los tres ejes y se toma el que menos
  // varianza deja; suficiente para saber si el aro esta retorcido o no
  let mejor = null;
  [{x:1,y:0,z:0},{x:0,y:1,z:0},{x:0,y:0,z:1},
   {x:1,y:1,z:0},{x:1,y:0,z:1},{x:0,y:1,z:1},
   {x:1,y:1,z:1},{x:1,y:-1,z:0},{x:1,y:0,z:-1},{x:0,y:1,z:-1}].forEach((seed) => {
    let v = norm(seed);
    for (let it = 0; it < 60; it++) {
      // v <- (tr*I - S) v  (potencia sobre el complemento: converge al eje menor)
      const tr = sxx + syy + szz;
      const nv = {
        x: tr*v.x - (sxx*v.x + sxy*v.y + sxz*v.z),
        y: tr*v.y - (sxy*v.x + syy*v.y + syz*v.z),
        z: tr*v.z - (sxz*v.x + syz*v.y + szz*v.z),
      };
      v = norm(nv);
    }
    const q = sxx*v.x*v.x + syy*v.y*v.y + szz*v.z*v.z
            + 2*(sxy*v.x*v.y + sxz*v.x*v.z + syz*v.y*v.z);
    if (!mejor || q < mejor.q) mejor = { q: q, v: v };
  });
  const nrm = mejor.v;
  o.plano = Math.sqrt(mejor.q / aro.length) / palm;
  // hacia donde mira el agujero respecto a la palma
  o.miraFrente = Math.abs(dot(nrm, frente));
  o.miraAncho = Math.abs(dot(nrm, ancho));
  o.miraLargo = Math.abs(dot(nrm, largo));

  // ---- cierre del aro --------------------------------------------------
  const t1 = P('Thumb1_036'), t2 = P('Thumb2_037');
  const t3 = P('Thumb3_038'), t4 = P('Thumb4_039');
  const tips = ['Index4_043','Middle4_047','Ring4_051','Pinky4_055'].map(P);
  o.cierre = dist(t4, tips[0]) / palm;
  o.cierreM = dist(t4, tips[1]) / palm;
  // yema contra yema: la pulpa del pulgar toca la del indice, y la punta del
  // indice puede caer en cualquier parte de la ultima falange del pulgar
  o.pinza = Math.min(
    aSeg(tips[0], t3, t4) / palm,
    aSeg(t4, P('Index3_042'), tips[0]) / palm
  );

  // ---- los cuatro dedos ------------------------------------------------
  const K = ['Index1_040','Middle1_044','Ring1_048','Pinky1_052'].map(P);
  const A = ['Index2_041','Middle2_045','Ring2_049','Pinky2_053'].map(P);
  const C = ['Index3_042','Middle3_046','Ring3_050','Pinky3_054'].map(P);
  const mcp = [], pip = [], dip = [], alPulgar = [];
  for (let i = 0; i < 4; i++) {
    mcp.push(grados(largo, sub(A[i], K[i])));
    pip.push(grados(sub(A[i], K[i]), sub(C[i], A[i])));
    dip.push(grados(sub(C[i], A[i]), sub(tips[i], C[i])));
    alPulgar.push(aSeg(tips[i], t3, t4) / palm);
  }
  o.mcp = mcp; o.pip = pip; o.dip = dip;
  o.arco = [media(mcp), media(pip), media(dip)];
  o.mcpDisp = disp(mcp); o.pipDisp = disp(pip); o.dipDisp = disp(dip);
  o.alPulgar = alPulgar;
  // los cuatro dedos van juntos, como un solo bloque curvo
  o.gaps = [dist(tips[0],tips[1])/palm, dist(tips[1],tips[2])/palm, dist(tips[2],tips[3])/palm];
  o.gapMin = Math.min.apply(null, o.gaps);
  o.gapDisp = disp(o.gaps);
  o.knuGaps = [dist(K[0],K[1])/palm, dist(K[1],K[2])/palm, dist(K[2],K[3])/palm];

  // ---- el pulgar -------------------------------------------------------
  const anchoLen = len(anchoV) || 1;
  const marco = (p) => ({
    across: dot(sub(p, knuI), ancho) / anchoLen,
    frente: dot(sub(p, knuI), frente) / palm,
    alto: dot(sub(p, wrist), largo) / palm,
  });
  ['1','2','3','4'].forEach((k, i) => {
    const m = marco([t1, t2, t3, t4][i]);
    o['across' + k] = m.across;
    o['frente' + k] = m.frente;
    o['alto' + k] = m.alto;
  });
  o.mpAng = grados(sub(t2, t1), sub(t3, t2));
  o.ipAng = grados(sub(t3, t2), sub(t4, t3));
  o.dobla = grados(sub(t2, t1), sub(t4, t3));
  // en la O el pulgar SUBE hasta la altura de las yemas y se queda del lado
  // del indice; si cruza hacia el menique la mano se lee como E/M/N
  o.sube = o.alto4 - o.alto2;
  o.cruza = o.across4 - o.across2;
  o.altoYemas = media(tips.map((p) => dot(sub(p, wrist), largo) / palm));
  o.bajoYemas = o.altoYemas - o.alto4;

  // ---- el agujero TAL COMO SE VE ---------------------------------------
  // Un aro perfecto en 3D puede verse como una raya si mira de canto a la
  // camara. Se proyecta el aro y se mide el area del poligono en pantalla.
  if (cam) {
    const m = cam.projectionMatrix.elements, v = cam.matrixWorldInverse.elements;
    const mvp = new Array(16);
    for (let i = 0; i < 4; i++) for (let j = 0; j < 4; j++) {
      let s = 0;
      for (let k = 0; k < 4; k++) s += m[k*4+j] * v[i*4+k];
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
      const a2 = aro.map(pr), w2 = pr(wrist), k2 = pr(knuI);
    if (a2.every(Boolean) && w2 && k2) {
      const pl = Math.hypot(w2.x-k2.x, w2.y-k2.y) || 1;
      let area = 0;
      for (let i = 0; i < a2.length; i++) {
        const p = a2[i], q = a2[(i+1) % a2.length];
        area += p.x*q.y - q.x*p.y;
      }
      o.areaPantalla = Math.abs(area) / 2 / (pl*pl);
      const c2 = {
        x: media(a2.map((p) => p.x)),
        y: media(a2.map((p) => p.y)),
      };
      const r2 = a2.map((p) => Math.hypot(p.x-c2.x, p.y-c2.y) / pl);
      o.radioPantalla = media(r2);
      o.redondezPantalla = disp(r2) / (media(r2) || 1);
      o.cierrePantalla = Math.hypot(a2[3].x-a2[4].x, a2[3].y-a2[4].y) / pl;
    }
  }
  return o;
}
"""
)


HUESOS = [
    "Thumb1_036", "Thumb2_037", "Thumb3_038", "Thumb4_039",
    "Index1_040", "Index2_041", "Index3_042", "Index4_043",
    "Middle1_044", "Middle2_045", "Middle3_046", "Middle4_047",
    "Ring1_048", "Ring2_049", "Ring3_050", "Ring4_051",
    "Pinky1_052", "Pinky2_053", "Pinky3_054", "Pinky4_055",
]

# Posicion de cada hueso en el marco de la palma (muneca al origen, ejes
# largo/ancho/frente, unidad = largo de la palma). El marco lo fijan la muneca
# y la fila de nudillos, que no se mueven al doblar dedos ni pulgar: por eso
# las coordenadas de los dedos y las del pulgar se pueden medir por separado y
# juntarlas despues sin volver a renderizar cada combinacion.
MARCO_JS = (
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
    const b = B['mixamorig1RightHand' + n];
    if (!b) return null;
    const e = b.matrixWorld.elements;
    return { x: e[12], y: e[13], z: e[14] };
  };
  const sub = (a, b) => ({ x: a.x-b.x, y: a.y-b.y, z: a.z-b.z });
  const mul = (a, k) => ({ x: a.x*k, y: a.y*k, z: a.z*k });
  const dot = (a, b) => a.x*b.x + a.y*b.y + a.z*b.z;
  const cross = (a, b) => ({ x: a.y*b.z-a.z*b.y, y: a.z*b.x-a.x*b.z, z: a.x*b.y-a.y*b.x });
  const len = (a) => Math.hypot(a.x, a.y, a.z);
  const norm = (a) => { const l = len(a) || 1; return mul(a, 1/l); };

  const wrist = P('_035'), knuI = P('Index1_040'), knuP = P('Pinky1_052');
  if (!wrist || !knuI || !knuP) return { error: 'faltan-huesos' };
  const palm = len(sub(knuI, wrist)) || 1;
  const u = norm(sub(knuI, wrist));
  let w = sub(knuP, knuI);
  w = norm(sub(w, mul(u, dot(w, u))));
  const v = cross(u, w);

  const out = { palm: palm };
  """
    + json.dumps(HUESOS)
    + """.forEach((n) => {
    const p = P(n);
    if (!p) return;
    const d = sub(p, wrist);
    out[n.split('_')[0]] = [dot(d, u)/palm, dot(d, w)/palm, dot(d, v)/palm];
  });
  return out;
}
"""
)


def _f(vals, dec=2):
    return "[" + " ".join(f"{v:+.{dec}f}" for v in vals) + "]"


def linea(nombre, o, score=None):
    s = f"score={score:6.3f} " if score is not None else ""
    return (
        f"{nombre:24s} {s}cierre={o['cierre']:.3f} pinza={o['pinza']:.3f} "
        f"radio={o['radio']:.3f} redondez={o['redondez']:.3f} plano={o['plano']:.3f} "
        f"area={o.get('areaPantalla', 0):.3f} gap={o['gapMin']:.3f}"
    )


def detalle(o):
    return (
        f"    arco  mcp={o['arco'][0]:5.1f} pip={o['arco'][1]:5.1f} dip={o['arco'][2]:5.1f}"
        f"   disp {o['mcpDisp']:4.1f}/{o['pipDisp']:4.1f}/{o['dipDisp']:4.1f}\n"
        f"    dedos mcp={_f(o['mcp'], 1)} pip={_f(o['pip'], 1)} dip={_f(o['dip'], 1)}\n"
        f"    yemas alPulgar={_f(o['alPulgar'], 3)} gaps={_f(o['gaps'], 3)}"
        f" (nudillos {_f(o['knuGaps'], 3)})\n"
        f"    pulgar across={_f([o['across1'], o['across2'], o['across3'], o['across4']])}"
        f" frente={_f([o['frente1'], o['frente2'], o['frente3'], o['frente4']])}\n"
        f"           alto={_f([o['alto1'], o['alto2'], o['alto3'], o['alto4']])}"
        f" mp={o['mpAng']:.0f} ip={o['ipAng']:.0f} dobla={o['dobla']:.0f}"
        f" bajoYemas={o['bajoYemas']:+.2f}\n"
        f"    mira  frente={o['miraFrente']:.2f} ancho={o['miraAncho']:.2f}"
        f" largo={o['miraLargo']:.2f}"
        + (
            f"\n    yemas (alto across frente) indice={_f(o['yemaI'])}"
            f" pulgar={_f(o['yemaT'])}"
            if "yemaI" in o
            else ""
        )
    )


DEDOS = ("Index", "Middle", "Ring", "Pinky")


def metricas(marco):
    """Las mismas medidas que MEDIDA_O_JS, pero desde el marco de la palma.

    Permite juntar un barrido de dedos con uno de pulgar sin renderizar cada
    combinacion: el marco no depende de como esten doblados ni unos ni otro.
    """
    P = {k: np.asarray(v, float) for k, v in marco.items() if k != "palm"}
    largo = np.array([1.0, 0.0, 0.0])
    aro = np.array([P[n] for n in
                    ("Thumb1", "Thumb2", "Thumb3", "Thumb4",
                     "Index4", "Index3", "Index2", "Index1")])

    o = {}
    centro = aro.mean(axis=0)
    radios = np.linalg.norm(aro - centro, axis=1)
    o["radio"] = float(radios.mean())
    o["redondez"] = float(np.ptp(radios) / (radios.mean() or 1))

    vals, vecs = np.linalg.eigh(np.cov((aro - centro).T, bias=True))
    nrm = vecs[:, 0]
    o["plano"] = float(np.sqrt(max(vals[0], 0.0)))
    o["miraLargo"], o["miraAncho"], o["miraFrente"] = (abs(float(c)) for c in nrm)

    t = [P[f"Thumb{i}"] for i in (1, 2, 3, 4)]
    tips = [P[d + "4"] for d in DEDOS]
    K = [P[d + "1"] for d in DEDOS]
    A = [P[d + "2"] for d in DEDOS]
    C = [P[d + "3"] for d in DEDOS]

    o["cierre"] = float(np.linalg.norm(t[3] - tips[0]))
    o["cierreM"] = float(np.linalg.norm(t[3] - tips[1]))
    o["pinza"] = min(_a_seg(tips[0], t[2], t[3]), _a_seg(t[3], C[0], tips[0]))

    o["mcp"] = [_grados(largo, A[i] - K[i]) for i in range(4)]
    o["pip"] = [_grados(A[i] - K[i], C[i] - A[i]) for i in range(4)]
    o["dip"] = [_grados(C[i] - A[i], tips[i] - C[i]) for i in range(4)]
    o["arco"] = [sum(o[k]) / 4 for k in ("mcp", "pip", "dip")]
    for k in ("mcp", "pip", "dip"):
        o[k + "Disp"] = max(o[k]) - min(o[k])
    o["alPulgar"] = [_a_seg(p, t[2], t[3]) for p in tips]
    o["gaps"] = [float(np.linalg.norm(tips[i] - tips[i + 1])) for i in range(3)]
    o["gapMin"] = min(o["gaps"])
    o["gapDisp"] = max(o["gaps"]) - min(o["gaps"])
    o["knuGaps"] = [float(np.linalg.norm(K[i] - K[i + 1])) for i in range(3)]

    ancho = float(P["Pinky1"][1] - P["Index1"][1]) or 1.0
    marco_pt = lambda p: [
        float(p[0]),
        float((p[1] - P["Index1"][1]) / ancho),
        float(p[2] - P["Index1"][2]),
    ]
    for i in range(4):
        o[f"alto{i+1}"], o[f"across{i+1}"], o[f"frente{i+1}"] = marco_pt(t[i])
    o["yemaI"] = marco_pt(tips[0])
    o["yemaT"] = marco_pt(t[3])
    o["mpAng"] = _grados(t[1] - t[0], t[2] - t[1])
    o["ipAng"] = _grados(t[2] - t[1], t[3] - t[2])
    o["dobla"] = _grados(t[1] - t[0], t[3] - t[2])
    o["sube"] = o["alto4"] - o["alto2"]
    o["cruza"] = o["across4"] - o["across2"]
    o["altoYemas"] = float(sum(p[0] for p in tips) / 4)
    o["bajoYemas"] = o["altoYemas"] - o["alto4"]
    return o


def _grados(u, v):
    nu = float(np.linalg.norm(u)) or 1.0
    nv = float(np.linalg.norm(v)) or 1.0
    return float(np.degrees(np.arccos(np.clip(float(u @ v) / (nu * nv), -1, 1))))


def _a_seg(p, a, b):
    ab = b - a
    l2 = float(ab @ ab) or 1.0
    k = min(1.0, max(0.0, float((p - a) @ ab) / l2))
    return float(np.linalg.norm(p - (a + ab * k)))


def banda(v, lo, hi):
    """0 dentro de [lo, hi]; crece linealmente fuera."""
    if v is None:
        return 1.0
    if v < lo:
        return lo - v
    if v > hi:
        return v - hi
    return 0.0


def puntuar(o):
    """Menor es mejor. Los pesos siguen lo que se ve en la lamina.

    Manda el contacto YEMA CON YEMA. Solo con `pinza` (distancia de la yema del
    indice al cuerpo del pulgar) la busqueda se conformaba con que el indice
    apoyara a media altura del pulgar, y entonces el pulgar seguia de largo y
    sobresalia por la derecha como una barra: el contorno dejaba de leerse como
    O. `cierre` (punta contra punta) es lo que cierra el aro de verdad.
    """
    p = 0.0
    p += 10.0 * banda(o["cierre"], 0.0, 0.13)
    p += 8.0 * banda(o["pinza"], 0.0, 0.09)
    p += 5.0 * banda(o["radio"], 0.30, 0.52)     # agujero visible, no un puno
    p += 3.0 * banda(o["redondez"], 0.0, 0.75)
    p += 3.0 * banda(o["plano"], 0.0, 0.10)
    if o.get("areaPantalla") is not None:
        p += 3.0 * banda(o["areaPantalla"], 0.20, 1.20)
    # Los cuatro dedos, curvos y parejos, sin abrirse en abanico. Las bandas
    # son anchas a proposito: con el techo del MCP en 62 la puntuacion
    # descartaba (10 puntos de castigo) la variante que en la hoja de
    # contactos era la que mas se parecia a la lamina.
    p += 2.5 * banda(o["arco"][0], 45.0, 72.0)
    p += 2.0 * banda(o["arco"][1], 48.0, 82.0)
    p += 1.5 * banda(o["arco"][2], 22.0, 48.0)
    p += 0.04 * o["mcpDisp"] + 0.03 * o["pipDisp"] + 0.02 * o["dipDisp"]
    p += 5.0 * banda(o["gapMin"], 0.10, 0.24)
    p += 4.0 * banda(o["gapDisp"], 0.0, 0.08)
    # el pulgar se curva sobre si mismo; recto se ve como un palo cruzado
    p += 2.5 * banda(o["dobla"], 55.0, 105.0)
    # sube hasta las yemas y se queda del lado del indice
    p += 3.0 * banda(o["cruza"], -0.05, 0.45)
    p += 2.0 * banda(o["bajoYemas"], -0.18, 0.18)
    p += 2.0 * banda(o["ipAng"], 0.0, 70.0)      # falange final no rota
    return p
