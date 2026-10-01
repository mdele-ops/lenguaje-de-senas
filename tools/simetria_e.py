"""Medidas de simetria de los cuatro dedos de la E.

Las busquedas anteriores (search_e9..e14) puntuaban la letra con minimos y
maximos: "que ningun dedo se atraviese", "que la yema mas alta baje lo
suficiente". Eso deja pasar poses donde un dedo cierra distinto del vecino,
que es justo lo que se ve mal en pantalla: la fila de yemas sale escalonada.

Aqui se mide la DISPERSION entre los cuatro dedos, en 3D y en la imagen:
  fold/front/across   por dedo, normalizados al largo de la palma
  *_disp              max-min de esas cuatro medidas (0 = fila perfecta)
  gapDisp             que tan iguales son los tres huecos entre yemas vecinas
"""
from pose_lab_e import _GET_SCENE

SIMETRIA_JS = (
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
  const d = (a, b) => Math.hypot(a.x-b.x, a.y-b.y, a.z-b.z);
  const disp = (v) => Math.max.apply(null, v) - Math.min.apply(null, v);

  const K = ['Index1_040','Middle1_044','Ring1_048','Pinky1_052'].map(P);
  const A = ['Index2_041','Middle2_045','Ring2_049','Pinky2_053'].map(P);
  const C = ['Index3_042','Middle3_046','Ring3_050','Pinky3_054'].map(P);
  const T = ['Index4_043','Middle4_047','Ring4_051','Pinky4_055'].map(P);
  const wrist = P('_035');
  const palm = d(wrist, K[0]) || 1;
  // Marco de la palma. Hace falta porque la E lleva un `extra` en el brazo
  // (arm z=-18) que gira la mano entera: medir alturas en Y del mundo daria
  // numeros que no se pueden comparar con letras que no llevan ese giro.
  const lg = { x: (K[0].x-wrist.x)/palm, y: (K[0].y-wrist.y)/palm, z: (K[0].z-wrist.z)/palm };
  const anV = { x: K[3].x-K[0].x, y: K[3].y-K[0].y, z: K[3].z-K[0].z };
  const anL = Math.hypot(anV.x, anV.y, anV.z) || 1;
  const an = { x: anV.x/anL, y: anV.y/anL, z: anV.z/anL };
  const fr = {
    x: lg.y*an.z - lg.z*an.y,
    y: lg.z*an.x - lg.x*an.z,
    z: lg.x*an.y - lg.y*an.x,
  };
  const proy = (u, e) => (u.x*e.x + u.y*e.y + u.z*e.z);

  // eje transversal de la palma: del nudillo del indice al del menique
  const al2 = anV.x*anV.x + anV.y*anV.y + anV.z*anV.z || 1;
  const along = (p) => ((p.x-K[0].x)*anV.x + (p.y-K[0].y)*anV.y + (p.z-K[0].z)*anV.z) / al2;

  const o = { palm: palm };
  const fold = [], front = [], across = [], mcpAng = [], pipAng = [], dipAng = [];
  // angulo entre dos vectores, en grados
  const entre = (u, v) => {
    const nu = Math.hypot(u.x,u.y,u.z) || 1, nv = Math.hypot(v.x,v.y,v.z) || 1;
    const cs = (u.x*v.x + u.y*v.y + u.z*v.z) / (nu*nv);
    return Math.acos(Math.max(-1, Math.min(1, cs))) * 180 / Math.PI;
  };
  const seg = (a, b) => ({ x: b.x-a.x, y: b.y-a.y, z: b.z-a.z });
  for (let i = 0; i < 4; i++) {
    // fold: cuanto baja la yema respecto a su nudillo a lo largo de la palma
    // front: cuanto se separa de la palma hacia la cara palmar
    fold.push(proy({ x: K[i].x-T[i].x, y: K[i].y-T[i].y, z: K[i].z-T[i].z }, lg) / palm);
    front.push(proy({ x: T[i].x-K[i].x, y: T[i].y-K[i].y, z: T[i].z-K[i].z }, fr) / palm);
    across.push(along(T[i]));
    mcpAng.push(entre(lg, seg(K[i], A[i])));
    pipAng.push(entre(seg(K[i], A[i]), seg(A[i], C[i])));
    dipAng.push(entre(seg(A[i], C[i]), seg(C[i], T[i])));
  }
  const media = (v) => v.reduce((a, b) => a + b, 0) / v.length;
  o.fold = fold; o.front = front; o.across = across;
  o.foldMedia = media(fold);
  o.frontMedia = media(front);
  o.mcpAng = mcpAng; o.pipAng = pipAng; o.dipAng = dipAng;
  o.foldDisp = disp(fold);
  o.frontDisp = disp(front);
  o.mcpDisp = disp(mcpAng);
  o.pipDisp = disp(pipAng);
  o.dipDisp = disp(dipAng);

  // huecos entre yemas vecinas, en 3D
  const gaps = [d(T[0],T[1])/palm, d(T[1],T[2])/palm, d(T[2],T[3])/palm];
  o.gaps = gaps;
  o.gapMin = Math.min.apply(null, gaps);
  o.gapDisp = disp(gaps);
  // el mismo hueco medido en los nudillos: es el ancho "natural" de la mano
  o.knuGaps = [d(K[0],K[1])/palm, d(K[1],K[2])/palm, d(K[2],K[3])/palm];

  // ---- lo mismo, proyectado a la imagen -------------------------------------
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
    const t2 = T.map(pr), k2 = K.map(pr), w2 = pr(wrist);
    const palm2 = Math.hypot(w2.x-k2[0].x, w2.y-k2[0].y) || 1;
    const alturas = [], xs = [];
    for (let i = 0; i < 4; i++) {
      alturas.push((k2[i].y - t2[i].y) / palm2);
      xs.push(t2[i].x / palm2);
    }
    o.scrFold = alturas;
    o.scrFoldDisp = disp(alturas);
    const g2 = [Math.abs(xs[1]-xs[0]), Math.abs(xs[2]-xs[1]), Math.abs(xs[3]-xs[2])];
    o.scrGaps = g2;
    o.scrGapMin = Math.min.apply(null, g2);
    o.scrGapDisp = disp(g2);
  }
  return o;
}
"""
)


def _f(vals, dec=2):
    return "[" + " ".join(f"{v:+.{dec}f}" for v in vals) + "]"


def informe(nombre, s):
    """Una linea por pose con las dispersiones, y el detalle por dedo debajo."""
    cab = (
        f"{nombre:26s} fold={s['foldMedia']:.3f} front={s['frontMedia']:.3f} "
        f"foldD={s['foldDisp']:.3f} frontD={s['frontDisp']:.3f} "
        f"mcpD={s['mcpDisp']:5.1f} pipD={s['pipDisp']:5.1f} dipD={s['dipDisp']:5.1f} "
        f"gap={s['gapMin']:.3f}/D{s['gapDisp']:.3f}"
    )
    if "scrFoldDisp" in s:
        cab += (
            f" | pantalla foldD={s['scrFoldDisp']:.3f} "
            f"gap={s['scrGapMin']:.3f}/D{s['scrGapDisp']:.3f}"
        )
    return cab


def detalle(s):
    return (
        f"    fold={_f(s['fold'])} front={_f(s['front'])} across={_f(s['across'])}\n"
        f"    mcp={_f(s['mcpAng'], 1)} pip={_f(s['pipAng'], 1)} dip={_f(s['dipAng'], 1)}\n"
        f"    gaps={_f(s['gaps'], 3)} (nudillos {_f(s['knuGaps'], 3)})"
    )


def score_simetria(s):
    """Menor es mejor. Solo penaliza el desajuste entre dedos."""
    p = 0.0
    p += 10.0 * s["foldDisp"]
    p += 6.0 * s["frontDisp"]
    p += 0.06 * s["pipDisp"]
    p += 0.04 * s["dipDisp"]
    p += 8.0 * s["gapDisp"]
    if "scrFoldDisp" in s:
        p += 10.0 * s["scrFoldDisp"]
        p += 8.0 * s["scrGapDisp"]
    return p
