"""Medidas del pulgar de la E en el marco de la palma.

Las busquedas anteriores puntuaban el pulgar solo por su PUNTA (`across`,
`tipoI`, `pulgarBajoYemas`). Con eso la punta acaba donde toca, pero el resto
del dedo puede quedar despegado de la palma: en el render el pulgar sale por el
borde de la mano como un cuerno. Aqui se mide cada articulacion del pulgar, no
solo la punta:

    across_*   0 = nudillo del indice, 1 = nudillo del menique (a lo ancho)
    frente_*   cuanto se separa de la palma hacia la camara
    alto_*     a lo largo de la palma, 0 = fila de nudillos
    ipAng      doblez de la ultima falange (en un pulgar real no pasa de ~80)
"""
from pose_lab_e import _GET_SCENE

PULGAR_JS = (
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
  const dot = (a, b) => a.x*b.x + a.y*b.y + a.z*b.z;
  const len = (a) => Math.hypot(a.x, a.y, a.z);
  const norm = (a) => { const l = len(a) || 1; return { x: a.x/l, y: a.y/l, z: a.z/l }; };
  const cross = (a, b) => ({ x: a.y*b.z-a.z*b.y, y: a.z*b.x-a.x*b.z, z: a.x*b.y-a.y*b.x });
  const dist = (a, b) => len(sub(a, b));
  const grados = (u, v) =>
    Math.acos(Math.max(-1, Math.min(1, dot(norm(u), norm(v))))) * 180 / Math.PI;

  const wrist = P('_035');
  const knuI = P('Index1_040'), knuP = P('Pinky1_052');
  const palm = dist(wrist, knuI) || 1;
  const largo = norm(sub(knuI, wrist));
  const anchoV = sub(knuP, knuI);
  const ancho = norm(anchoV);
  const frente = norm(cross(largo, ancho));
  const anchoLen = len(anchoV) || 1;

  const t1 = P('Thumb1_036'), t2 = P('Thumb2_037');
  const t3 = P('Thumb3_038'), t4 = P('Thumb4_039');
  const tips = ['Index4_043','Middle4_047','Ring4_051','Pinky4_055'].map(P);
  const knuM = P('Middle1_044');

  // `alto` se mide desde la MUÑECA (0 = muneca, 1 = nudillo del indice), no
  // desde la fila de nudillos: la fila es oblicua -el nudillo del menique
  // queda 0.2 mas abajo que el del indice- y usarla como origen daba numeros
  // que no se podian comparar con lo medido en la foto.
  const o = {};
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

  // lo que hace el "cuerno": la articulacion mas despegada de la palma y la
  // que mas se sale por el borde del indice
  o.frenteMax = Math.max(o.frente2, o.frente3, o.frente4);
  // si alguna articulacion se va por detras del plano de la palma, el pulgar
  // esta metido dentro de la mano y en el render desaparece o la atraviesa
  o.frenteMin = Math.min(o.frente2, o.frente3, o.frente4);
  o.acrossMin = Math.min(o.across2, o.across3, o.across4);
  // el pulgar tiene que quedar POR DETRAS de las yemas: son ellas las que se
  // apoyan encima. Si sobresale, en pantalla tapa los dedos.
  o.frenteYemas = Math.max.apply(null, tips.map(
    (p) => dot(sub(p, knuI), frente) / palm
  ));
  o.asomaSobreYemas = o.frenteMax - o.frenteYemas;
  // doblez de las dos ultimas articulaciones del pulgar
  o.mpAng = grados(sub(t2, t1), sub(t3, t2));
  o.ipAng = grados(sub(t3, t2), sub(t4, t3));

  // Cuanto se dobla el pulgar ENTERO sobre si mismo: angulo entre el primer
  // tramo y el ultimo. Pasado de ~80 grados el dedo se cierra en anillo y en
  // el render aparece un agujero en medio de la palma.
  o.dobla = grados(sub(t2, t1), sub(t4, t3));
  // El pulgar de la E SUBE hacia los dedos y CRUZA hacia el menique: los tres
  // puntos tienen que ir en ese orden. Si no, la punta acaba apuntando hacia
  // la muneca, que es lo contrario de la foto.
  o.sube = o.alto4 - o.alto2;
  o.subeIP = o.alto3 - o.alto2;
  o.cruza = o.across4 - o.across2;
  o.cruzaIP = o.across3 - o.across2;

  // relacion con las yemas: en la E se apoyan encima del pulgar
  const alto = (p) => dot(sub(p, wrist), largo) / palm;
  o.altoYemas = tips.map(alto).reduce((a, b) => a + b, 0) / tips.length;
  o.bajoYemas = o.altoYemas - o.alto4;
  o.tipoI = dist(t4, tips[0]) / palm;
  o.tipoM = dist(t4, tips[1]) / palm;
  o.yemaAlPulgar = Math.min.apply(null, tips.map((p) => {
    const ab = sub(t4, t2);
    const l2 = dot(ab, ab) || 1;
    let t = dot(sub(p, t2), ab) / l2;
    t = Math.max(0, Math.min(1, t));
    return dist(p, { x: t2.x+ab.x*t, y: t2.y+ab.y*t, z: t2.z+ab.z*t }) / palm;
  }));

  // --- lo mismo, pero EN PANTALLA -------------------------------------
  // Las medidas de arriba viven en el marco 3D de la palma y no se pueden
  // comparar con la foto: en la E los dedos se doblan hacia la camara, asi que
  // "el pulgar esta por debajo de las yemas" mezcla altura y profundidad. Lo
  // que se ve -y lo que juzga quien mira- es la proyeccion, asi que la altura
  // del pulgar se puntua aqui, en el mismo encuadre en que se midio la foto.
  const cam = scene.camera || (scene.getCamera && scene.getCamera());
  if (cam) {
    cam.updateMatrixWorld(true);
    const pm = cam.projectionMatrix.elements, vm = cam.matrixWorldInverse.elements;
    const mvp = new Array(16);
    for (let i = 0; i < 4; i++) for (let j = 0; j < 4; j++) {
      let s = 0;
      for (let k = 0; k < 4; k++) s += pm[k*4+j] * vm[i*4+k];
      mvp[i*4+j] = s;
    }
    const pr = (p) => {
      const w = mvp[3]*p.x + mvp[7]*p.y + mvp[11]*p.z + mvp[15] || 1;
      return {
        x: (mvp[0]*p.x + mvp[4]*p.y + mvp[8]*p.z + mvp[12]) / w,
        y: (mvp[1]*p.x + mvp[5]*p.y + mvp[9]*p.z + mvp[13]) / w,
      };
    };
    const r = mv.getBoundingClientRect();
    // a pixeles, que es en lo que se midio la foto (y hacia abajo)
    const px = (p) => { const q = pr(p); return { x: q.x*r.width/2, y: -q.y*r.height/2 }; };
    const s2 = (a, b) => ({ x: a.x-b.x, y: a.y-b.y });
    const d2 = (a, b) => Math.hypot(a.x-b.x, a.y-b.y);
    const n2 = (a) => { const l = Math.hypot(a.x, a.y) || 1; return { x: a.x/l, y: a.y/l }; };

    const w2 = px(wrist), kM = px(knuM), kI = px(knuI), kP = px(knuP);
    const palmPx = d2(w2, kM) || 1;
    // eje largo de la palma en pantalla y su perpendicular hacia el pulgar
    const arriba = n2(s2(kM, w2));
    const haciaPulgar = n2(s2(kI, kP));
    const enMarco = (p) => {
      const q = s2(px(p), w2);
      return {
        alto: (q.x*arriba.x + q.y*arriba.y) / palmPx,
        ancho: (q.x*haciaPulgar.x + q.y*haciaPulgar.y) / palmPx,
      };
    };
    const yemas = tips.map(enMarco);
    const p4 = enMarco(t4), p3 = enMarco(t3), p2 = enMarco(t2);
    o.pantAlto = p4.alto;
    o.pantAncho = p4.ancho;
    o.pantAltoIP = p3.alto;
    o.pantAnchoIP = p3.ancho;
    o.pantBajoYemas =
      yemas.reduce((a, b) => a + b.alto, 0) / yemas.length - p4.alto;

    // Como se ve TUMBADO el pulgar. En la lamina de referencia es una barra
    // horizontal corta justo debajo de las yemas, apuntando hacia el menique;
    // sin medir esto la busqueda daba por bueno un pulgar en diagonal, que es
    // lo que se veia mal aunque la punta cayera donde tocaba.
    //   0 grados  = horizontal y apuntando al menique (lo que se quiere)
    //  90 grados  = de pie, apuntando a los dedos
    // 180 grados  = horizontal pero apuntando al lado del pulgar
    const eje = { ancho: p4.ancho - p3.ancho, alto: p4.alto - p3.alto };
    o.pantInclina = Math.atan2(eje.alto, -eje.ancho) * 180 / Math.PI;
    // largo del tramo visible del pulgar: del nudillo a la yema, en pantalla
    o.pantLargo = Math.hypot(p4.ancho - p2.ancho, p4.alto - p2.alto);
  }
  return o;
}
"""
)


def linea(nombre, m, score=None):
    txt = (
        f"{nombre:30s} "
        f"pant: incl={m['pantInclina']:+6.1f} largo={m['pantLargo']:.2f} "
        f"yema={m['pantAlto']:+.2f},{m['pantAncho']:+.2f} "
        f"ip={m['pantAltoIP']:+.2f},{m['pantAnchoIP']:+.2f} "
        f"bajoYemas={m['pantBajoYemas']:+.2f} | "
        f"frente={m['frente2']:+.2f}/{m['frente3']:+.2f}/{m['frente4']:+.2f} "
        f"asoma={m['asomaSobreYemas']:+.2f} "
        f"mp={m['mpAng']:5.1f} ip={m['ipAng']:5.1f} dobla={m['dobla']:5.1f}"
    )
    if score is not None:
        txt = f"{txt} sc={score:6.3f}"
    return txt


def banda(v, lo, hi):
    if v < lo:
        return lo - v
    if v > hi:
        return v - hi
    return 0.0


# Bandas leidas sobre la foto ampliada (tools/zoom_ref_e/E_usuario2_x8.png).
# Se midieron los pixeles y se pasaron a unidades de palma (muneca = 0, nudillo
# del indice = 1 a lo largo; nudillo del indice = 0, nudillo del menique = 1 a
# lo ancho). Referencias del encuadre: muneca y=680, fila de nudillos y=290,
# nudillo del indice x=570, nudillo del menique x=270.
#
# Medido sobre la lamina de referencia del proyecto
# (tools/screenshots/referencia/E.png), que es la que manda: la foto del
# usuario esta tomada de mas abajo y ahi el pulgar se ve escorzado, lo que me
# llevo a leerlo como una diagonal cuando en realidad va HORIZONTAL.
#
# Marco de pantalla: origen en la muneca, "alto" hacia el nudillo del medio,
# "ancho" hacia el lado del pulgar, dividido por el largo de la palma
# proyectado (300 px en esa lamina).
#
#                        alto     ancho
#   uña del pulgar (t4)   0.92      0.05
#   nudillo IP     (t3)   0.90      0.30
#   nudillo MP     (t2)   0.97      0.47
#   media de las yemas    1.23        -
#
# O sea: el pulgar es una BARRA HORIZONTAL corta pegada justo debajo de las
# yemas, apuntando hacia el menique, con las puntas de los cuatro dedos
# apoyadas encima. Los tres nudillos estan casi a la misma altura -de ahi que
# se vea horizontal- y solo cruza media mano, no la palma entera.
# Solo se puntua lo que en la foto se VE sin ambiguedad. Las posiciones
# absolutas de la base y del nudillo IP se quitaron a proposito: en la foto
# esas dos articulaciones estan tapadas por los dedos, se estimaron a ojo y
# resultaron estar peleadas con la anatomia del esqueleto (la base del pulgar
# de este rig no baja de ~0.6 de palma sin despegarse). Fijandolas, la busqueda
# tenia que elegir entre altura y quedar plano, y sacaba el pulgar al aire.
BANDAS = {
    # --- donde SE VE el pulgar (marco de pantalla, como la foto) ---------
    # La yema queda media palma por debajo de las de los dedos y algo hacia su
    # lado. En 3D esto no se puede pedir: la base del pulgar de este esqueleto
    # ya nace por encima de las yemas dobladas, asi que exigirlo en el marco de
    # la palma no tiene solucion y la busqueda acababa sacando el pulgar al
    # aire para cumplirlo.
    # Que se vea TUMBADO y CORTO. Son las dos medidas que mandan: sin ellas
    # la busqueda daba por bueno un pulgar en diagonal cruzando la palma
    # entera, que cae donde toca pero no se parece a la lamina.
    "pantInclina": (-25, 25),
    "pantLargo": (0.30, 0.52),
    # Solo se pide la posicion RELATIVA a las yemas, no la altura absoluta:
    # en la lamina las yemas caen a 1.23 de palma y en el modelo a 0.76 porque
    # el puno cierra mas, asi que pedir las dos cosas a la vez no tiene
    # solucion y era lo que hacia rebotar la busqueda de un extremo a otro.
    # Lo cerrado que va el puno se decidio antes, al calibrar los dedos.
    "pantBajoYemas": (0.20, 0.42),
    "pantAncho": (-0.10, 0.20),
    "pantAnchoIP": (0.18, 0.44),
    # --- y como esta puesto en el espacio -------------------------------
    # Tumbado contra la palma. En cuanto se afloja, la busqueda saca el pulgar
    # hacia la camara como el de "OK".
    "frenteMax": (0.00, 0.42),
    # el hueso puede quedar casi en el plano de la palma: lo que se ve en el
    # render es la carne, que tiene grosor. Solo se castiga hundirse de verdad.
    "frenteMin": (-0.10, 0.35),
    # los dedos doblados se apoyan ENCIMA del pulgar, nunca al reves
    "asomaSobreYemas": (-1.00, 0.10),
    # tumbado, no enrollado: es lo que evita el anillo en medio de la palma
    "dobla": (0, 90),
    "ipAng": (0, 60),
    "mpAng": (10, 70),
}

PESOS = {
    "pantInclina": 0.35,
    "pantLargo": 25.0,
    "pantBajoYemas": 14.0,
    "pantAncho": 10.0,
    "pantAnchoIP": 6.0,
    "frenteMax": 14.0,
    "frenteMin": 10.0,
    "asomaSobreYemas": 10.0,
    "dobla": 0.25,
    "ipAng": 0.06,
    "mpAng": 0.05,
}


def puntuar(m):
    """Menor es mejor: suma de lo que cada medida se sale de su banda."""
    return sum(peso * banda(m[k], *BANDAS[k]) for k, peso in PESOS.items())
