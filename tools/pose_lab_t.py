"""T lab 1: medidas del puno con el pulgar METIDO entre indice y medio.

La T y la S son el mismo puno y solo cambia el pulgar, asi que hay que medir la
diferencia, no mirarla:

  S  el pulgar va TUMBADO por delante de las falanges medias y la yema apunta
     al anular: cruza el puno entero (thU ~ 0.6) y se queda por DEBAJO de lo
     mas alto del puno.
  T  el pulgar va DE PIE y se mete en el hueco que dejan el indice y el medio:
     la yema sale por arriba, entre esos dos dedos (thU ~ 0.2), y es el punto
     mas alto de la mano.

Lo que hace falta medir:

  thU / camU   posicion de la yema en el eje nudillo indice (0) -> nudillo
               menique (1), en 3D y en pantalla. El hueco indice-medio cae
               sobre uHueco (~0.17 con los nudillos repartidos).
  desvio       lo que se aparta la yema de ese hueco. Es LA medida de la letra.
  cima         cuanto asoma la yema por encima de lo mas alto del puno. En la
               S es negativo (el pulgar no asoma); en la lamina de la T la yema
               es el punto mas alto, asi que tiene que ser positivo.
  gapIdx/gapMed  separacion real entre la cadena del pulgar y la del indice y
               la del medio. Los huesos van por el centro de la carne: por
               debajo de ~0.12 las mallas se atraviesan. Estar "entre" los dos
               dedos es tener las DOS parecidas y ninguna por debajo de eso.
  huecoIM      lo que separan entre si las cadenas del indice y del medio. Si
               no se abre, el pulgar no cabe y la unica salida es atravesar un
               dedo; por eso hay que barrer tambien el `spread` de esos dos.
  thUpDir      hacia donde mira el ultimo tramo del pulgar: +1 = de pie (T),
               0 = tumbado cruzando (S).
"""
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from pose_lab_e import ARM, BONES, T1, T2, T3, _GET_SCENE, free_camera
import search_e9 as se9
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "lab_t"
OUT.mkdir(parents=True, exist_ok=True)

se9.URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=t1"

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
    if (!b || !b.matrixWorld) return null;
    const e = b.matrixWorld.elements;
    return { x: e[12], y: e[13], z: e[14] };
  };
  const sub = (a, b) => ({ x: a.x-b.x, y: a.y-b.y, z: a.z-b.z });
  const dot = (a, b) => a.x*b.x + a.y*b.y + a.z*b.z;
  const cross = (a, b) => ({
    x: a.y*b.z - a.z*b.y,
    y: a.z*b.x - a.x*b.z,
    z: a.x*b.y - a.y*b.x,
  });
  const norm = (v) => {
    const l = Math.hypot(v.x, v.y, v.z) || 1;
    return { x: v.x/l, y: v.y/l, z: v.z/l };
  };
  const d = (a, b) => Math.hypot(a.x-b.x, a.y-b.y, a.z-b.z);

  // Distancia entre dos segmentos. Con puntos sueltos el pulgar puede
  // atravesar un dedo entre falange y falange sin que ninguna medida se entere.
  const segSeg = (p1, q1, p2, q2) => {
    const d1 = sub(q1, p1), d2 = sub(q2, p2), r = sub(p1, p2);
    const a = dot(d1, d1), e = dot(d2, d2), f = dot(d2, r);
    const c = dot(d1, r), b = dot(d1, d2);
    const den = a*e - b*b;
    let s = den > 1e-12 ? Math.min(1, Math.max(0, (b*f - c*e) / den)) : 0;
    let t = (b*s + f) / (e || 1);
    if (t < 0) { t = 0; s = Math.min(1, Math.max(0, -c / (a || 1))); }
    else if (t > 1) { t = 1; s = Math.min(1, Math.max(0, (b - c) / (a || 1))); }
    const c1 = { x: p1.x + d1.x*s, y: p1.y + d1.y*s, z: p1.z + d1.z*s };
    const c2 = { x: p2.x + d2.x*t, y: p2.y + d2.y*t, z: p2.z + d2.z*t };
    return Math.hypot(c1.x-c2.x, c1.y-c2.y, c1.z-c2.z);
  };

  const wrist = P('mixamorig1RightHand_035');
  const knu = {
    I: P('mixamorig1RightHandIndex1_040'), M: P('mixamorig1RightHandMiddle1_044'),
    R: P('mixamorig1RightHandRing1_048'),  P: P('mixamorig1RightHandPinky1_052'),
  };
  const pip = {
    I: P('mixamorig1RightHandIndex2_041'), M: P('mixamorig1RightHandMiddle2_045'),
    R: P('mixamorig1RightHandRing2_049'),  P: P('mixamorig1RightHandPinky2_053'),
  };
  const dip = {
    I: P('mixamorig1RightHandIndex3_042'), M: P('mixamorig1RightHandMiddle3_046'),
    R: P('mixamorig1RightHandRing3_050'),  P: P('mixamorig1RightHandPinky3_054'),
  };
  const tip = {
    I: P('mixamorig1RightHandIndex4_043'), M: P('mixamorig1RightHandMiddle4_047'),
    R: P('mixamorig1RightHandRing4_051'),  P: P('mixamorig1RightHandPinky4_055'),
  };
  const t1 = P('mixamorig1RightHandThumb1_036');
  const t2 = P('mixamorig1RightHandThumb2_037');
  const t3 = P('mixamorig1RightHandThumb3_038');
  const t4 = P('mixamorig1RightHandThumb4_039');
  const palm = d(wrist, knu.I) || 1;

  // --- marco de la mano ---------------------------------------------------
  const lat = sub(knu.P, knu.I);
  const latLen = Math.hypot(lat.x, lat.y, lat.z) || 1;
  const latN = { x: lat.x/latLen, y: lat.y/latLen, z: lat.z/latLen };
  const u = (p) => dot(sub(p, knu.I), latN) / latLen;
  const upN = norm(sub(knu.M, wrist));           // muneca -> nudillos
  const nrm = norm(cross(sub(knu.P, knu.I), sub(knu.M, wrist)));
  const fre = { x: -nrm.x, y: -nrm.y, z: -nrm.z }; // lado palmar = frente del puno

  const o = { palm: palm };

  // --- el puno cerrado ----------------------------------------------------
  o.punoMax = Math.max(
    d(tip.I, wrist), d(tip.M, wrist), d(tip.R, wrist), d(tip.P, wrist)
  ) / palm;

  // --- donde esta el hueco indice-medio -----------------------------------
  o.uIdx = u(knu.I);
  o.uMed = u(knu.M);
  o.uHueco = (o.uIdx + o.uMed) / 2;

  // --- donde esta la yema del pulgar --------------------------------------
  o.thU = u(t4);
  o.thUbase = u(t2);
  o.desvio = o.thU - o.uHueco;   // 0 = justo en el hueco

  // --- altura: en la T la yema asoma por arriba ---------------------------
  const alt = (p) => dot(sub(p, knu.I), upN) / palm;
  let cima = -9;
  ['I','M','R','P'].forEach((k) => {
    [knu[k], pip[k], dip[k], tip[k]].forEach((p) => { cima = Math.max(cima, alt(p)); });
  });
  o.cimaPuno = cima;
  o.cima = alt(t4) - cima;       // >0 = la yema es el punto mas alto
  o.altYema = alt(t4);
  o.altIP = alt(t3);

  // --- orientacion del pulgar ---------------------------------------------
  const eje = norm(sub(t4, t2));
  o.thUpDir = dot(eje, upN);     // +1 = de pie (T)
  o.thLatDir = dot(eje, latN);   // +1 = tumbado cruzando (S)
  o.thFreDir = dot(eje, fre);
  // cuanto se dobla el pulgar sobre si mismo: pasado de ~90 sale el anillo
  const v1 = norm(sub(t2, t1)), v2 = norm(sub(t4, t3));
  o.dobla = Math.acos(Math.max(-1, Math.min(1, dot(v1, v2)))) * 180 / Math.PI;

  // --- profundidad: metido en el hueco, ni delante ni detras --------------
  const freDe = (p) => dot(sub(p, knu.I), fre) / palm;
  let freMax = -9;
  ['I','M','R','P'].forEach((k) => {
    [knu[k], pip[k], dip[k], tip[k]].forEach((p) => { freMax = Math.max(freMax, freDe(p)); });
  });
  o.freMax = freMax;
  o.sobreFrente = freDe(t4) - freMax;   // >0 = por delante del puno (eso es la S)

  // --- separaciones entre cadenas -----------------------------------------
  const cad = {
    I: [[knu.I, pip.I], [pip.I, dip.I], [dip.I, tip.I]],
    M: [[knu.M, pip.M], [pip.M, dip.M], [dip.M, tip.M]],
    R: [[knu.R, pip.R], [pip.R, dip.R], [dip.R, tip.R]],
    P: [[knu.P, pip.P], [pip.P, dip.P], [dip.P, tip.P]],
  };
  const pulgar = [[t1, t2], [t2, t3], [t3, t4]];
  // `tramos` deja elegir que parte del pulgar se mide. Hace falta separarlas:
  // la BASE del pulgar y la del indice son vecinas en cualquier mano, tambien
  // en la lamina, asi que castigar la distancia minima de la cadena entera
  // descarta poses que en pantalla no tienen ningun problema. Lo que de verdad
  // no puede pasar es que se metan una en otra las partes que se VEN, o sea
  // los dos ultimos tramos del pulgar.
  const gapCon = (k, tramos) => {
    let g = 9;
    cad[k].forEach((seg) => {
      tramos.forEach((th) => {
        g = Math.min(g, segSeg(th[0], th[1], seg[0], seg[1]) / palm);
      });
    });
    return g;
  };
  o.gapIdx = gapCon('I', pulgar);
  o.gapMed = gapCon('M', pulgar);
  o.gapRing = gapCon('R', pulgar);
  o.gapPinky = gapCon('P', pulgar);
  // solo la parte visible del pulgar (falange media + distal)
  const punta = [[t2, t3], [t3, t4]];
  o.gapIdxPunta = gapCon('I', punta);
  o.gapMedPunta = gapCon('M', punta);
  o.gapBase = Math.min(gapCon('I', [[t1, t2]]), gapCon('M', [[t1, t2]]));
  o.gapMin = Math.min(o.gapIdx, o.gapMed, o.gapRing, o.gapPinky);
  // "entre los dos dedos" = tocar a los dos por igual
  o.simetria = Math.abs(o.gapIdxPunta - o.gapMedPunta);

  // hueco disponible entre indice y medio: si no se abre, el pulgar no cabe
  let hueco = 9;
  cad.I.forEach((a) => {
    cad.M.forEach((b) => { hueco = Math.min(hueco, segSeg(a[0], a[1], b[0], b[1]) / palm); });
  });
  o.huecoIM = hueco;
  // y el de los otros pares, para no abrir el abanico entero
  let huecoMR = 9, huecoRP = 9;
  cad.M.forEach((a) => {
    cad.R.forEach((b) => { huecoMR = Math.min(huecoMR, segSeg(a[0], a[1], b[0], b[1]) / palm); });
  });
  cad.R.forEach((a) => {
    cad.P.forEach((b) => { huecoRP = Math.min(huecoRP, segSeg(a[0], a[1], b[0], b[1]) / palm); });
  });
  o.huecoMR = huecoMR;
  o.huecoRP = huecoRP;

  // --- y lo mismo visto por la camara -------------------------------------
  // Es lo que el usuario juzga, y no depende del signo de la normal.
  //
  // Todo esto va en PIXELES del visor, no en coordenadas de recorte (NDC). El
  // visor de la pagina es un rectangulo ancho (unos 863x419), asi que una
  // unidad de NDC en x y una en y no miden lo mismo: dividir una altura en
  // NDC-y por un ancho en NDC-x multiplica el resultado por la relacion de
  // aspecto, y "el pulgar asoma 0.25" acaba siendo 0.12 de verdad. En pixeles
  // los dos ejes miden igual y las medidas se pueden comparar con lo que se ve.
  const cma = scene.camera || (scene.getCamera && scene.getCamera());
  if (cma) {
    cma.updateMatrixWorld(true);
    if (cma.updateProjectionMatrix) cma.updateProjectionMatrix();
    const vi = cma.matrixWorldInverse.elements;
    const pr = cma.projectionMatrix.elements;
    const rect = mv.getBoundingClientRect();
    const mul = (e, p) => ({
      x: e[0]*p.x + e[4]*p.y + e[8]*p.z + e[12]*p.w,
      y: e[1]*p.x + e[5]*p.y + e[9]*p.z + e[13]*p.w,
      z: e[2]*p.x + e[6]*p.y + e[10]*p.z + e[14]*p.w,
      w: e[3]*p.x + e[7]*p.y + e[11]*p.z + e[15]*p.w,
    });
    const ver = (p) => {
      const v = mul(vi, { x: p.x, y: p.y, z: p.z, w: 1 });
      const c = mul(pr, v);
      return {
        z: -v.z / palm,
        px: (c.x / c.w * 0.5 + 0.5) * rect.width,
        py: (1 - (c.y / c.w * 0.5 + 0.5)) * rect.height,
      };
    };
    const vT4 = ver(t4), vKI = ver(knu.I), vKM = ver(knu.M), vKP = ver(knu.P);
    // ancho del puno en pixeles: la unidad en la que se dan las demas
    const ancho = vKP.px - vKI.px || 1;
    o.camAncho = Math.abs(ancho);
    o.camU = (vT4.px - vKI.px) / ancho;
    o.camUhueco = ((vKI.px + vKM.px) / 2 - vKI.px) / ancho;
    o.camDesvio = o.camU - o.camUhueco;
    // py crece hacia ABAJO, asi que lo mas alto del puno es el py mas pequeño
    let cimaPy = 1e9;
    ['I','M','R','P'].forEach((k) => {
      [knu[k], pip[k], dip[k], tip[k]].forEach((p) => {
        cimaPy = Math.min(cimaPy, ver(p).py);
      });
    });
    o.camCima = (cimaPy - vT4.py) / Math.abs(ancho);  // >0 = la yema asoma
    // profundidad: >0 = el pulgar esta por delante de los dedos (como en la S)
    o.camDelante = Math.min(ver(pip.I).z, ver(pip.M).z) - vT4.z;
  }
  return o;
}
"""
)


FINGERS = ("index", "middle", "ring", "pinky")


def pose_t(cierre=0.95, tcurl=0.35, taside=0.0, ttwist=None, tspread=None,
           thumb=None, spread=None, dedos=None, wrist=None, arm_z=-18):
    """Puno cerrado con el pulgar libre para levantarlo entre indice y medio.

    `thumb` son rotaciones crudas por hueso del pulgar, `spread` los grados de
    abanico por dedo (index, middle, ring, pinky) y `dedos` retoques por
    falange, {dedo: {posicion: {...}}} con 0 = nudillo.
    """
    ex = {ARM: {"z": arm_z}}
    for name, rot in (thumb or {}).items():
        ex[name] = dict(ex.get(name, {}), **rot)
    for dedo, rots in (dedos or {}).items():
        for i, rot in rots.items():
            hueso = BONES[dedo][i]
            ex[hueso] = dict(ex.get(hueso, {}), **rot)

    th = {"curl": tcurl, "aside": taside}
    if ttwist is not None:
        th["twist"] = ttwist
    if tspread is not None:
        th["spread"] = tspread

    sp = spread or (0, 0, 0, 0)
    pose = {"thumb": th, "extra": ex}
    for i, dedo in enumerate(FINGERS):
        pose[dedo] = {"curl": cierre}
        if sp[i]:
            pose[dedo]["spread"] = sp[i]
    if wrist:
        pose["muneca"] = dict(wrist)
    return pose


def linea(nombre, m):
    return (
        f"{nombre:22s} thU={m['thU']:+6.2f} desv={m['desvio']:+6.2f} "
        f"cima={m['cima']:+6.2f} up={m['thUpDir']:+5.2f} lat={m['thLatDir']:+5.2f} "
        f"gI={m['gapIdx']:.3f} gM={m['gapMed']:.3f} hIM={m['huecoIM']:.3f} "
        f"sobre={m['sobreFrente']:+.2f} puno={m['punoMax']:.2f}"
    )


def main():
    catalogo = json.loads((ROOT / "data" / "catalogo-lsm.json").read_text("utf-8"))
    por_letra = {s["letra"]: s for s in catalogo["senas"]}

    casos = {
        "00_T_actual": por_letra["T"]["pose"],
        "01_S_actual": por_letra["S"]["pose"],
        "02_A_actual": por_letra["A"]["pose"],
        "03_base": pose_t(),
    }

    # Que hace cada mando del pulgar por separado: hace falta saber cual lo
    # LEVANTA (thUpDir alto) y cual lo lleva de lado hasta el hueco.
    for c in (0.1, 0.3, 0.5, 0.7):
        casos[f"curl_{c}"] = pose_t(tcurl=c)
    for a in (-0.8, -0.4, 0.4, 0.8):
        casos[f"aside_{a}"] = pose_t(taside=a)
    for t in (-40, -20, 20, 40):
        casos[f"twist_{t}"] = pose_t(ttwist=t)
    for s in (-40, -20, 20, 40):
        casos[f"spread_{s}"] = pose_t(tspread=s)

    # Ejes crudos de los tres huesos del pulgar.
    for hueso, etiqueta in ((T1, "T1"), (T2, "T2"), (T3, "T3")):
        for eje in ("x", "y", "z"):
            for g in (-60, -30, 30, 60):
                casos[f"{etiqueta}_{eje}{g:+d}"] = pose_t(thumb={hueso: {eje: g}})

    # Y el abanico de indice y medio, que es lo que abre (o no) el hueco.
    for s in (-16, -8, 8, 16):
        casos[f"sepIM_{s}"] = pose_t(spread=(s, -s, 0, 0))

    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 1000, "height": 900})
        time.sleep(0.4)
        free_camera(page)

        medidas = {}
        for nombre, pose in casos.items():
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
            time.sleep(0.24)
            m = page.evaluate(MEASURE_JS)
            if m.get("error"):
                print(" ", nombre, m)
                continue
            medidas[nombre] = m
            print(" ", linea(nombre, m))

        browser.close()

    (OUT / "_casos.json").write_text(json.dumps(casos, indent=2), "utf-8")
    (OUT / "_medidas.json").write_text(json.dumps(medidas, indent=2), "utf-8")
    print("\nDatos en", OUT)


if __name__ == "__main__":
    main()
