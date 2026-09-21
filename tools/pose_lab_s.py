"""S lab 1: medidas del puno con el pulgar cruzado por delante.

La S de la lamina es un puno cerrado con el pulgar TUMBADO cruzando por
delante de las falanges medias, con la yema apuntando hacia el medio/anular.
Lo que hay hoy en el catalogo es `thumb.curl = 0.9` sobre un puno, que en este
rig se limita a plegar el pulgar contra su costado: sale una A apretada, no una
S, porque el pulgar nunca llega a pasar por delante de los dedos.

Para poder buscar la pose hace falta medir esas cosas por separado:

  thU        posicion de la yema del pulgar en el eje nudillo indice (0) ->
             nudillo menique (1). En la A el pulgar se queda en su costado
             (thU ~ 0); en la S tiene que haber cruzado hasta el medio.
  delanteIdx la yema del pulgar por delante de la falange media del indice,
  delanteMed medido sobre la normal de la palma. Positivo = el pulgar monta
             POR DELANTE, que es lo que hace la letra; negativo = se ha metido
             dentro del puno (eso es una T).
  thLatDir   hacia donde apunta el ultimo tramo del pulgar. En la S va tumbado
             cruzando (+1 = del indice hacia el menique); en la A sube (~0).
  gapDedos   separacion minima pulgar-dedos. 0 = las mallas se atraviesan.
"""
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from pose_lab_e import ARM, BONES, T1, T2, T3, _GET_SCENE, free_camera
import search_e9 as se9
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "lab_s"
OUT.mkdir(parents=True, exist_ok=True)

se9.URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=s1"

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

  // distancia entre dos segmentos: con puntos sueltos el pulgar puede
  // atravesar un dedo entre falange y falange sin que se note
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
  const distSeg = (p, a, b) => {
    const ab = sub(b, a), ap = sub(p, a);
    const l2 = dot(ab, ab) || 1;
    let t = Math.max(0, Math.min(1, dot(ap, ab) / l2));
    return Math.hypot(p.x-(a.x+ab.x*t), p.y-(a.y+ab.y*t), p.z-(a.z+ab.z*t));
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

  // --- ejes de la mano ----------------------------------------------------
  // lateral: del nudillo del indice al del menique (0 -> 1)
  const lat = sub(knu.P, knu.I);
  const latLen = Math.hypot(lat.x, lat.y, lat.z) || 1;
  const latN = { x: lat.x/latLen, y: lat.y/latLen, z: lat.z/latLen };
  const u = (p) => dot(sub(p, knu.I), latN) / latLen;
  // largo: de la muneca a los nudillos
  const upN = norm(sub(knu.M, wrist));
  // normal de la palma; en estos labs sale por el DORSO
  const nrm = norm(cross(sub(knu.P, knu.I), sub(knu.M, wrist)));
  // el frente del puno (donde quedan las falanges medias) es el lado PALMAR,
  // o sea -nrm: es ahi donde tiene que tumbarse el pulgar
  const fre = { x: -nrm.x, y: -nrm.y, z: -nrm.z };

  const o = { palm: palm };

  // --- el puno tiene que estar cerrado ------------------------------------
  o.punoMax = Math.max(
    d(tip.I, wrist), d(tip.M, wrist), d(tip.R, wrist), d(tip.P, wrist)
  ) / palm;
  o.punoMin = Math.min(
    d(tip.I, wrist), d(tip.M, wrist), d(tip.R, wrist), d(tip.P, wrist)
  ) / palm;

  // --- el pulgar cruza por delante ----------------------------------------
  o.thU = u(t4);          // yema: 0 = costado del indice, 1 = menique
  o.thUbase = u(t2);      // nudillo del pulgar
  o.cruza = o.thU - o.thUbase;   // cuanto avanza cruzando

  // cuanto monta la yema por delante de cada falange media
  o.delanteIdx = dot(sub(t4, pip.I), fre) / palm;
  o.delanteMed = dot(sub(t4, pip.M), fre) / palm;
  // y el cuerpo del pulgar (nudillo IP) sobre el indice
  o.delanteIP = dot(sub(t3, pip.I), fre) / palm;

  // --- orientacion del pulgar ---------------------------------------------
  const eje = norm(sub(t4, t2));
  o.thLatDir = dot(eje, latN);   // +1 = tumbado del indice hacia el menique
  o.thUpDir = dot(eje, upN);     // +1 = de pie, como en la A
  o.thFreDir = dot(eje, fre);

  // altura de la yema respecto a las falanges medias: la S cruza a esa
  // altura, ni por los nudillos ni por la base de la palma
  o.altYema = dot(sub(t4, pip.I), upN) / palm;
  o.altYemaMed = dot(sub(t4, pip.M), upN) / palm;

  // --- contacto sin atravesar ---------------------------------------------
  const cad = {
    I: [[knu.I, pip.I], [pip.I, dip.I], [dip.I, tip.I]],
    M: [[knu.M, pip.M], [pip.M, dip.M], [dip.M, tip.M]],
    R: [[knu.R, pip.R], [pip.R, dip.R], [dip.R, tip.R]],
    P: [[knu.P, pip.P], [pip.P, dip.P], [dip.P, tip.P]],
  };
  const pulgar = [[t1, t2], [t2, t3], [t3, t4]];
  let gap = 9;
  Object.keys(cad).forEach((k) => {
    cad[k].forEach((seg) => {
      pulgar.forEach((th) => {
        gap = Math.min(gap, segSeg(th[0], th[1], seg[0], seg[1]) / palm);
      });
    });
  });
  o.gapDedos = gap;
  // apoyo: lo cerca que va el pulgar de las falanges medias de indice y medio
  o.apoyoIdx = distSeg(t4, pip.I, dip.I) / palm;
  o.apoyoMed = distSeg(t3, pip.M, dip.M) / palm;

  // --- que no se salga del puno -------------------------------------------
  o.thFuera = dot(sub(t4, knu.I), fre) / palm;
  o.anchoPuno = latLen / palm;

  // --- como esta plegado el propio dedo ------------------------------------
  // Sin esto no se puede calibrar nada: "delante de los dedos" solo significa
  // algo si se sabe hasta donde llega el frente del puno. pipFre es lo que
  // sobresale la falange media (el frente sobre el que se tumba el pulgar) y
  // puntaFre donde acaba la yema, que en un puno vuelve hacia la palma.
  o.pipFre = dot(sub(pip.I, knu.I), fre) / palm;
  o.puntaFre = dot(sub(tip.I, knu.I), fre) / palm;
  o.puntaAlt = dot(sub(tip.I, knu.I), upN) / palm;
  // yema del indice contra la base de la palma: en un puno cerrado se apoya
  o.puntaPalma = d(tip.I, wrist) / palm;

  // Punto mas adelantado de los cuatro dedos: es el "frente" real del puno.
  // Que el pulgar quede por delante de EL (sobreFrente > 0) es lo que hace la
  // S; comparar solo contra una falange suelta enganya en cuanto el puno se
  // cierra un poco mas o un poco menos.
  let freMax = -9;
  Object.keys(cad).forEach((k) => {
    [knu[k], pip[k], dip[k], tip[k]].forEach((p) => {
      freMax = Math.max(freMax, dot(sub(p, knu.I), fre) / palm);
    });
  });
  o.freMax = freMax;
  o.sobreFrente = dot(sub(t4, knu.I), fre) / palm - freMax;
  o.sobreFrenteIP = dot(sub(t3, knu.I), fre) / palm - freMax;

  // --- y lo mismo visto desde la camara ------------------------------------
  // El signo de la normal se hereda de los labs anteriores y es facil leerlo
  // al reves. Estas medidas no dependen de el: se proyecta con la matriz de la
  // camara y se compara la profundidad, que es literalmente lo que el usuario
  // ve. camDelante > 0 = el pulgar pasa por DELANTE de los dedos.
  const cma = scene.camera || (scene.getCamera && scene.getCamera());
  if (cma) {
    cma.updateMatrixWorld(true);
    if (cma.updateProjectionMatrix) cma.updateProjectionMatrix();
    const vi = cma.matrixWorldInverse.elements;
    const pr = cma.projectionMatrix.elements;
    const mul = (e, p) => ({
      x: e[0]*p.x + e[4]*p.y + e[8]*p.z + e[12]*p.w,
      y: e[1]*p.x + e[5]*p.y + e[9]*p.z + e[13]*p.w,
      z: e[2]*p.x + e[6]*p.y + e[10]*p.z + e[14]*p.w,
      w: e[3]*p.x + e[7]*p.y + e[11]*p.z + e[15]*p.w,
    });
    // distancia a la camara (en palmas) y posicion en pantalla, x hacia la
    // derecha y y hacia arriba, ambas en [-1, 1]
    const ver = (p) => {
      const v = mul(vi, { x: p.x, y: p.y, z: p.z, w: 1 });
      const c = mul(pr, v);
      return { z: -v.z / palm, sx: c.x / c.w, sy: c.y / c.w };
    };
    const vT4 = ver(t4), vI = ver(pip.I), vM = ver(pip.M);
    const vKI = ver(knu.I), vKP = ver(knu.P);
    o.camDelante = Math.min(vI.z, vM.z) - vT4.z;
    // recorrido del pulgar en pantalla entre el nudillo del indice (0) y el
    // del menique (1): asi se comprueba el cruce tal y como se ve
    const ancho = vKP.sx - vKI.sx || 1;
    o.camU = (vT4.sx - vKI.sx) / ancho;
    o.camUbase = (ver(t2).sx - vKI.sx) / ancho;
    // altura de la yema del pulgar respecto a las falanges medias
    o.camAlt = (vT4.sy - (vI.sy + vM.sy) / 2) / Math.abs(ancho);
    // ...y respecto a lo mas alto del puno: en la lamina el pulgar cruza por
    // delante de los dedos, no asoma por encima de ellos, asi que camCima
    // tiene que quedarse por debajo de 0
    let cima = -9;
    Object.keys(cad).forEach((k) => {
      [knu[k], pip[k], dip[k], tip[k]].forEach((p) => {
        cima = Math.max(cima, ver(p).sy);
      });
    });
    o.camCima = (vT4.sy - cima) / Math.abs(ancho);
  }
  return o;
}
"""
)


def pose_s(cierre=0.95, tcurl=0.55, taside=0.0, ttwist=None, tspread=None,
           thumb=None, dedos=None, wrist=None, arm_z=-18):
    """Puno cerrado con el pulgar libre para tumbarlo por delante.

    `thumb` es {hueso: {"x":..,"y":..,"z":..}} y `dedos` es
    {dedo: {posicion: {...}}} con la posicion 0 = nudillo, 1 = falange media.
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

    pose = {
        "thumb": th,
        "index": {"curl": cierre},
        "middle": {"curl": cierre},
        "ring": {"curl": cierre},
        "pinky": {"curl": cierre},
        "extra": ex,
    }
    if wrist:
        pose["muneca"] = dict(wrist)
    return pose


def linea(nombre, m):
    return (
        f"{nombre:22s} thU={m['thU']:+6.2f} cruza={m['cruza']:+6.2f} "
        f"delI={m['delanteIdx']:+6.3f} delM={m['delanteMed']:+6.3f} "
        f"lat={m['thLatDir']:+5.2f} up={m['thUpDir']:+5.2f} "
        f"alt={m['altYema']:+6.3f} gap={m['gapDedos']:.3f} "
        f"puno={m['punoMax']:.2f}"
    )


def main():
    catalogo = json.loads((ROOT / "data" / "catalogo-lsm.json").read_text("utf-8"))
    por_letra = {s["letra"]: s for s in catalogo["senas"]}

    casos = {
        "00_S_actual": por_letra["S"]["pose"],
        "01_A_actual": por_letra["A"]["pose"],
        "02_T_actual": por_letra["T"]["pose"],
        "03_R_pulgar": por_letra["R"]["pose"],
        "04_base": pose_s(),
    }

    # Que hace cada mando del pulgar por separado, para saber cual lo tumba
    # hacia delante y cual lo lleva de lado.
    for c in (0.3, 0.5, 0.7, 0.9):
        casos[f"curl_{c}"] = pose_s(tcurl=c)
    for a in (-0.8, -0.4, 0.4, 0.8):
        casos[f"aside_{a}"] = pose_s(tcurl=0.5, taside=a)
    for t in (-40, -20, 20, 40):
        casos[f"twist_{t}"] = pose_s(tcurl=0.5, ttwist=t)
    for s in (-40, -20, 20, 40):
        casos[f"spread_{s}"] = pose_s(tcurl=0.5, tspread=s)

    # Y los ejes crudos del nudillo del pulgar (T1) y de la falange (T2).
    for eje in ("x", "y", "z"):
        for g in (-60, -30, 30, 60):
            casos[f"T1_{eje}{g:+d}"] = pose_s(tcurl=0.4, thumb={T1: {eje: g}})
            casos[f"T2_{eje}{g:+d}"] = pose_s(tcurl=0.4, thumb={T2: {eje: g}})

    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 1000, "height": 900})
        time.sleep(0.4)
        free_camera(page)

        medidas = {}
        for nombre, pose in casos.items():
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
            time.sleep(0.26)
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
