"""Medidas de la E sobre el rig que carga hoy la pagina.

Los modulos viejos (`simetria_e`, `pulgar_e`, `pose_lab_e`) buscan los huesos
con los nombres del .glb anterior (`mixamorig1RightHandIndex1_040`). El modelo
que sirve `practica.html` ahora es `model2.glb`, cuyos huesos van sin prefijo ni
sufijo (`RightHandIndex1`), asi que aquellas medidas devuelven null. Aqui se
repite lo que hacia falta con los nombres actuales.

Marco de la palma: origen en la muneca, `largo` hacia el nudillo del medio,
`ancho` del nudillo del indice al del menique, `frente` saliendo por la cara
palmar. Todo en unidades de palma (muneca -> nudillo del medio = 1).
"""
from pose_lab_e import _GET_SCENE

FINGERS = ("index", "middle", "ring", "pinky")
DEDOS = {
    "index": ["RightHandIndex1", "RightHandIndex2", "RightHandIndex3", "RightHandIndex4"],
    "middle": ["RightHandMiddle1", "RightHandMiddle2", "RightHandMiddle3", "RightHandMiddle4"],
    "ring": ["RightHandRing1", "RightHandRing2", "RightHandRing3", "RightHandRing4"],
    "pinky": ["RightHandPinky1", "RightHandPinky2", "RightHandPinky3", "RightHandPinky4"],
}
PULGAR = ["RightHandThumb1", "RightHandThumb2", "RightHandThumb3", "RightHandThumb4"]
MUNECA = "RightHand"

# Topes del rig (catalogo-lsm.json -> rig.flexMaxGrados) y grados que aporta un
# curl de 1.0 (rig.curlMaxGrados). Hacen falta para no pedir correcciones que
# el controlador va a recortar sin avisar.
CURL_MAX = {"prox": 72.0, "midd": 90.0, "dist": 68.0}
FLEX_MAX = {"prox": 80.0, "midd": 100.0, "dist": 70.0}
JUNTAS = ("prox", "midd", "dist")

MED_JS = (
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
  const grados = (u, v) =>
    Math.acos(Math.max(-1, Math.min(1, dot(nor(u), nor(v))))) * 180 / Math.PI;
  const disp = (v) => Math.max.apply(null, v) - Math.min.apply(null, v);
  const media = (v) => v.reduce((a, b) => a + b, 0) / v.length;

  const dedos = ['Index', 'Middle', 'Ring', 'Pinky'];
  const K = dedos.map((d) => P('RightHand' + d + '1'));
  const A = dedos.map((d) => P('RightHand' + d + '2'));
  const C = dedos.map((d) => P('RightHand' + d + '3'));
  const T = dedos.map((d) => P('RightHand' + d + '4'));
  const t1 = P('RightHandThumb1'), t2 = P('RightHandThumb2');
  const t3 = P('RightHandThumb3'), t4 = P('RightHandThumb4');
  const wrist = P('RightHand');
  if (!wrist || !K[0] || !t4) return { error: 'no-bones' };

  const palm = dist(wrist, K[1]) || 1;          // muneca -> nudillo del medio
  const largo = nor(sub(K[1], wrist));
  const anchoV = sub(K[3], K[0]);               // indice -> menique
  const anchoLen = len(anchoV) || 1;
  const ancho = nor(anchoV);
  // Cara palmar. El signo se fija con el pulgar en reposo, que nace por delante
  // de la palma: si saliera negativo el marco estaria del reves.
  let frente = nor(cruz(ancho, largo));
  if (dot(sub(t1, wrist), frente) < 0) frente = { x: -frente.x, y: -frente.y, z: -frente.z };

  const marco = (p) => ({
    alto: dot(sub(p, wrist), largo) / palm,
    ancho: dot(sub(p, K[0]), ancho) / anchoLen,
    frente: dot(sub(p, K[0]), frente) / palm,
  });

  const o = { palm: palm };
  const mcpAng = [], pipAng = [], dipAng = [], alto = [], frenteD = [], anchoD = [];
  for (let i = 0; i < 4; i++) {
    mcpAng.push(grados(largo, sub(A[i], K[i])));
    pipAng.push(grados(sub(A[i], K[i]), sub(C[i], A[i])));
    dipAng.push(grados(sub(C[i], A[i]), sub(T[i], C[i])));
    const m = marco(T[i]);
    alto.push(m.alto);        // 1 = fila de nudillos, 0 = muneca
    frenteD.push(m.frente);   // + = hacia la camara (cara palmar)
    anchoD.push(m.ancho);     // 0 = indice, 1 = menique
  }
  o.mcpAng = mcpAng; o.pipAng = pipAng; o.dipAng = dipAng;
  o.alto = alto; o.frente = frenteD; o.ancho = anchoD;
  // La fila de nudillos no es plana: en este rig el del menique nace mas abajo
  // que el del medio, asi que una yema puede parecer mal doblada solo porque su
  // raiz esta mas baja. `yemaRel` mide cada yema contra SU nudillo.
  o.knuAlto = K.map((k) => marco(k).alto);
  o.knuAltoDisp = disp(o.knuAlto);
  o.yemaRel = [0,1,2,3].map((i) => alto[i] - o.knuAlto[i]);
  o.yemaRelDisp = disp(o.yemaRel);
  o.mcpDisp = disp(mcpAng); o.pipDisp = disp(pipAng); o.dipDisp = disp(dipAng);
  o.altoDisp = disp(alto); o.frenteDisp = disp(frenteD);
  o.altoMedia = media(alto); o.frenteMedia = media(frenteD);

  // huecos entre yemas vecinas y entre nudillos (el ancho natural de la mano)
  o.gaps = [dist(T[0],T[1])/palm, dist(T[1],T[2])/palm, dist(T[2],T[3])/palm];
  o.gapMin = Math.min.apply(null, o.gaps);
  o.gapDisp = disp(o.gaps);
  o.knuGaps = [dist(K[0],K[1])/palm, dist(K[1],K[2])/palm, dist(K[2],K[3])/palm];

  // ---- pulgar --------------------------------------------------------------
  ['1','2','3','4'].forEach((k, i) => {
    const m = marco([t1, t2, t3, t4][i]);
    o['tAlto' + k] = m.alto;
    o['tAncho' + k] = m.ancho;
    o['tFrente' + k] = m.frente;
  });
  o.tFrenteMax = Math.max(o.tFrente2, o.tFrente3, o.tFrente4);
  o.tFrenteMin = Math.min(o.tFrente2, o.tFrente3, o.tFrente4);
  o.mpAng = grados(sub(t2, t1), sub(t3, t2));
  o.ipAng = grados(sub(t3, t2), sub(t4, t3));
  o.dobla = grados(sub(t2, t1), sub(t4, t3));
  o.tipoI = dist(t4, T[0]) / palm;
  // yema del pulgar contra el cuerpo de los dedos: min distancia a los tramos
  // C->T de los cuatro dedos (donde se apoya en la foto)
  o.tocaDedos = Math.min.apply(null, [0,1,2,3].map((i) => {
    const ab = sub(T[i], C[i]);
    const l2 = dot(ab, ab) || 1;
    let s = dot(sub(t4, C[i]), ab) / l2;
    s = Math.max(0, Math.min(1, s));
    return dist(t4, { x: C[i].x+ab.x*s, y: C[i].y+ab.y*s, z: C[i].z+ab.z*s }) / palm;
  }));

  // ---- lo mismo en pantalla (lo que se compara con la foto) ---------------
  if (cam) {
    const pm = cam.projectionMatrix.elements, vm = cam.matrixWorldInverse.elements;
    const mvp = new Array(16);
    for (let i = 0; i < 4; i++) for (let j = 0; j < 4; j++) {
      let s = 0;
      for (let k = 0; k < 4; k++) s += pm[k*4+j] * vm[i*4+k];
      mvp[i*4+j] = s;
    }
    const r = mv.getBoundingClientRect();
    const px = (p) => {
      const w = mvp[3]*p.x + mvp[7]*p.y + mvp[11]*p.z + mvp[15] || 1;
      return {
        x: (mvp[0]*p.x + mvp[4]*p.y + mvp[8]*p.z + mvp[12]) / w * r.width / 2,
        y: -(mvp[1]*p.x + mvp[5]*p.y + mvp[9]*p.z + mvp[13]) / w * r.height / 2,
      };
    };
    const s2 = (a, b) => ({ x: a.x-b.x, y: a.y-b.y });
    const d2 = (a, b) => Math.hypot(a.x-b.x, a.y-b.y);
    const n2 = (a) => { const l = Math.hypot(a.x, a.y) || 1; return { x: a.x/l, y: a.y/l }; };

    const w2 = px(wrist), kM = px(K[1]), kI = px(K[0]), kP = px(K[3]);
    const palmPx = d2(w2, kM) || 1;
    const arriba = n2(s2(kM, w2));
    const haciaPulgar = n2(s2(kI, kP));
    const enMarco = (p) => {
      const q = s2(px(p), w2);
      return {
        alto: (q.x*arriba.x + q.y*arriba.y) / palmPx,
        ancho: (q.x*haciaPulgar.x + q.y*haciaPulgar.y) / palmPx,
      };
    };
    const yemas = T.map(enMarco);
    const nud = K.map(enMarco);
    const p2 = enMarco(t2), p3 = enMarco(t3), p4 = enMarco(t4);
    o.pYemaAlto = yemas.map((y) => y.alto);
    o.pYemaAncho = yemas.map((y) => y.ancho);
    o.pYemaAltoDisp = disp(o.pYemaAlto);
    o.pNudAlto = media(nud.map((n) => n.alto));
    // cuanto bajan las yemas por debajo de la fila de nudillos, en pantalla
    o.pBajaYema = o.pNudAlto - media(o.pYemaAlto);
    o.pTAlto = p4.alto; o.pTAncho = p4.ancho;
    o.pTAltoIP = p3.alto; o.pTAnchoIP = p3.ancho;
    o.pTBajoYemas = media(o.pYemaAlto) - p4.alto;
    const eje = { ancho: p4.ancho - p3.ancho, alto: p4.alto - p3.alto };
    o.pTInclina = Math.atan2(eje.alto, -eje.ancho) * 180 / Math.PI;
    o.pTLargo = Math.hypot(p4.ancho - p2.ancho, p4.alto - p2.alto);
    // huecos entre yemas vecinas vistos de frente: en la E van juntas
    const xs = o.pYemaAncho;
    o.pGaps = [Math.abs(xs[1]-xs[0]), Math.abs(xs[2]-xs[1]), Math.abs(xs[3]-xs[2])];
    o.pGapMin = Math.min.apply(null, o.pGaps);
    o.pGapDisp = disp(o.pGaps);

    // Lo mismo pero medido en anchos de mano en vez de palmas. De la foto del
    // usuario se puede leer con fiabilidad la separacion yema-indice/yema-menique
    // (es una distancia dentro de la propia imagen), no la longitud de la palma,
    // que queda tapada por el puno. Con esta escala el objetivo no depende de
    // adivinar donde cae la muneca en la foto.
    const abanico = Math.abs(xs[0] - xs[3]) || 1;
    o.sAbanico = abanico;
    o.sTBajo = (media(o.pYemaAlto) - p4.alto) / abanico;
    o.sTAncho = (xs[0] - p4.ancho) / abanico;
    o.sTLargo = Math.hypot(p4.ancho - p3.ancho, p4.alto - p3.alto) / abanico;
    o.sYemaDisp = o.pYemaAltoDisp / abanico;
  }
  return o;
}
"""
)


def _f(vals, dec=2):
    return "[" + " ".join(f"{v:+.{dec}f}" for v in vals) + "]"


def informe(nombre, m):
    return (
        f"{nombre:22s} mcp={_f(m['mcpAng'], 0)} pip={_f(m['pipAng'], 0)} "
        f"dip={_f(m['dipAng'], 0)} D={m['mcpDisp']:.0f}/{m['pipDisp']:.0f}/{m['dipDisp']:.0f}"
    )


def detalle(m):
    txt = (
        f"    yemas alto={_f(m['alto'])} frente={_f(m['frente'])} ancho={_f(m['ancho'])}\n"
        f"    gaps={_f(m['gaps'], 3)} (nudillos {_f(m['knuGaps'], 3)})\n"
        f"    pulgar alto={m['tAlto2']:+.2f}/{m['tAlto3']:+.2f}/{m['tAlto4']:+.2f} "
        f"ancho={m['tAncho2']:+.2f}/{m['tAncho3']:+.2f}/{m['tAncho4']:+.2f} "
        f"frente={m['tFrente2']:+.2f}/{m['tFrente3']:+.2f}/{m['tFrente4']:+.2f}\n"
        f"    pulgar mp={m['mpAng']:.0f} ip={m['ipAng']:.0f} dobla={m['dobla']:.0f} "
        f"tocaDedos={m['tocaDedos']:.2f} tipoI={m['tipoI']:.2f}"
    )
    if "pTInclina" in m:
        txt += (
            f"\n    PANTALLA bajaYema={m['pBajaYema']:+.2f} yemaD={m['pYemaAltoDisp']:.3f} "
            f"gap={m['pGapMin']:.3f}/D{m['pGapDisp']:.3f}\n"
            f"    PANTALLA pulgar incl={m['pTInclina']:+.0f} largo={m['pTLargo']:.2f} "
            f"bajoYemas={m['pTBajoYemas']:+.2f} ancho={m['pTAncho']:+.2f}/"
            f"{m['pTAnchoIP']:+.2f}"
        )
    return txt
