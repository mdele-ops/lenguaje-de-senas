"""R lab 1: que eje cruza de verdad el indice y el medio en este rig.

En la lamina la R son dos dedos estirados hacia arriba y CRUZADOS: el medio
monta por delante del indice y las dos yemas se juntan arriba, mientras anular
y menique quedan cerrados con el pulgar encima. La pose que hay en el catalogo
usa `spread` +-35, que en este rig solo abre los dedos en V; nunca los cruza.

Antes de buscar la pose hay que saber que hace cada eje sobre el nudillo, asi
que este primer lab gira Index1/Middle1 en x, y, z por separado y mide:

  uIdx/uMed   posicion lateral de cada yema sobre el eje nudillo indice ->
              nudillo medio (0 = indice, 1 = medio). Si los dedos se cruzan,
              la yema del indice se pasa al lado del medio: uIdx > uMed.
  cruce       uIdx - uMed. Positivo = cruzados, que es lo que pide la letra.
  frenteMed   la yema del medio por delante del indice, en la normal de la
              palma. En la lamina el medio monta ENCIMA, no por detras.
  gap         distancia minima entre los dos dedos tomando las falanges como
              segmentos. 0 = se atraviesan; en un cruce real se rozan.
  altIdx/Med  cuanto sube la yema sobre su nudillo: los dos van estirados.
"""
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from pose_lab_e import ARM, BONES, _GET_SCENE, free_camera, HAND_POS_JS
import search_e9 as se9
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "lab_r"
OUT.mkdir(parents=True, exist_ok=True)

se9.URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=r1"

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

  // distancia entre dos segmentos en 3D (para saber si los dedos se tocan
  // o se atraviesan; con puntos sueltos el cruce se escapa entre falanges)
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
  const t4 = P('mixamorig1RightHandThumb4_039');
  const palm = d(wrist, knu.I) || 1;

  // eje lateral: del nudillo del indice al del medio (una "casilla" de nudillo)
  const lat = sub(knu.M, knu.I);
  const latLen = Math.hypot(lat.x, lat.y, lat.z) || 1;
  const latN = { x: lat.x/latLen, y: lat.y/latLen, z: lat.z/latLen };
  const u = (p) => dot(sub(p, knu.I), latN) / latLen;

  // normal de la palma (hacia donde mira la palma)
  const nrm = norm(cross(sub(knu.P, knu.I), sub(knu.M, wrist)));

  const o = { palm: palm };
  o.uIdx = u(tip.I);
  o.uMed = u(tip.M);
  o.uIdxPip = u(pip.I);
  o.uMedPip = u(pip.M);
  o.cruce = o.uIdx - o.uMed;
  o.crucePip = o.uIdxPip - o.uMedPip;

  // profundidad entre las dos yemas sobre la normal de la palma, que en estos
  // labs sale por el DORSO. Positivo = el medio esta mas atras, o sea que el
  // indice pasa por delante, que es lo que hace la lamina oficial de la LSM.
  o.frenteMed = dot(sub(tip.M, tip.I), nrm) / palm;
  o.frenteMedPip = dot(sub(pip.M, pip.I), nrm) / palm;
  // si el adelanto crece de la falange media a la yema, los dedos se abren en
  // V vista de perfil en vez de ir montados uno sobre otro
  o.abanico = o.frenteMed - o.frenteMedPip;
  o.sepYemas = d(tip.I, tip.M) / palm;

  // separacion minima entre las cadenas de los dos dedos
  const chI = [[knu.I, pip.I], [pip.I, dip.I], [dip.I, tip.I]];
  const chM = [[knu.M, pip.M], [pip.M, dip.M], [dip.M, tip.M]];
  let gap = 9;
  chI.forEach((a) => chM.forEach((b) => {
    gap = Math.min(gap, segSeg(a[0], a[1], b[0], b[1]) / palm);
  }));
  o.gap = gap;

  // estirados hacia arriba
  o.altIdx = (tip.I.y - knu.I.y) / palm;
  o.altMed = (tip.M.y - knu.M.y) / palm;
  o.vertIdx = norm(sub(tip.I, knu.I)).y;
  o.vertMed = norm(sub(tip.M, knu.M)).y;

  // anular y menique cerrados, pulgar encima
  o.punoMax = Math.max(d(tip.R, wrist), d(tip.P, wrist)) / palm;
  o.thumbSobre = d(t4, tip.R) / palm;
  o.thumbY = (t4.y - knu.I.y) / palm;
  // el pulgar de la lamina va TUMBADO sobre los dedos recogidos, no de canto:
  //   thLat   posicion de la yema en el eje de los nudillos. Negativo = se
  //           sale por el lado del indice, que es el pulgar en escuadra.
  //   thFuera cuanto se despega de la palma hacia el dorso/espectador.
  //   thHoriz 1 = pulgar tumbado, 0 = pulgar de pie.
  o.thLat = u(t4);
  o.thFuera = dot(sub(t4, knu.I), nrm) / palm;
  const th = sub(t4, P('mixamorig1RightHandThumb2_037'));
  o.thHoriz = Math.hypot(th.x, th.z) / (Math.hypot(th.x, th.y, th.z) || 1);
  return o;
}
"""
)


def pose_r(
    icurl=0.0,
    mcurl=0.0,
    cierre=0.95,
    tcurl=0.55,
    taside=0.0,
    idx=None,
    med=None,
    thumb=None,
    wrist=None,
    arm_z=-18,
):
    """Pose base de la R con rotaciones extra libres por hueso.

    idx/med son dicts {posicion: {"x":..,"y":..,"z":..}} donde la posicion es
    0 (nudillo), 1 (falange media) o 2 (distal).
    """
    ex = {ARM: {"z": arm_z}}
    for cadena, rots in ((BONES["index"], idx), (BONES["middle"], med)):
        for i, rot in (rots or {}).items():
            ex[cadena[i]] = dict(ex.get(cadena[i], {}), **rot)
    for name, rot in (thumb or {}).items():
        ex[name] = dict(ex.get(name, {}), **rot)

    pose = {
        "thumb": {"curl": tcurl, "aside": taside},
        "index": {"curl": icurl},
        "middle": {"curl": mcurl},
        "ring": {"curl": cierre},
        "pinky": {"curl": cierre},
        "extra": ex,
    }
    if wrist:
        pose["muneca"] = dict(wrist)
    return pose


def linea(nombre, m):
    return (
        f"{nombre:26s} uI={m['uIdx']:+6.2f} uM={m['uMed']:+6.2f} "
        f"cruce={m['cruce']:+6.2f} frente={m['frenteMed']:+6.2f} "
        f"gap={m['gap']:.3f} altI={m['altIdx']:+5.2f} altM={m['altMed']:+5.2f}"
    )


def main():
    catalogo = json.loads((ROOT / "data" / "catalogo-lsm.json").read_text("utf-8"))
    actual = next(s for s in catalogo["senas"] if s["letra"] == "R")["pose"]
    de_la_u = next(s for s in catalogo["senas"] if s["letra"] == "U")["pose"]

    casos = {"00_actual": actual, "01_U": de_la_u, "02_base": pose_r()}

    # Barrido de un eje cada vez sobre el nudillo del indice y del medio,
    # para ver cual mueve el dedo de lado (aduccion) y cual lo tuerce.
    for eje in ("x", "y", "z"):
        for g in (-30, -15, 15, 30):
            casos[f"idx_{eje}{g:+d}"] = pose_r(idx={0: {eje: g}})
            casos[f"med_{eje}{g:+d}"] = pose_r(med={0: {eje: -g}})

    # Y el par opuesto, que es como se cruzan de verdad dos dedos.
    for eje in ("x", "y", "z"):
        for g in (15, 30, 45):
            casos[f"par_{eje}{g}"] = pose_r(idx={0: {eje: g}}, med={0: {eje: -g}})

    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 1000, "height": 900})
        time.sleep(0.4)
        viewer = page.query_selector("#viewer")
        free_camera(page)

        for nombre, pose in casos.items():
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
            time.sleep(0.28)
            m = page.evaluate(MEASURE_JS)
            if m.get("error"):
                print(" ", nombre, m)
                continue
            print(" ", linea(nombre, m))

            mano = page.evaluate(HAND_POS_JS)
            for vista, orbit in (("frente", "0deg 84deg 0.50m"),
                                 ("lado", "-70deg 84deg 0.50m")):
                page.evaluate(
                    """(a) => {
                        const mv = document.getElementById('handViewer');
                        mv.cameraTarget = a.t;
                        mv.cameraOrbit = a.orbit;
                        mv.fieldOfView = a.fov;
                        mv.jumpCameraToGoal();
                    }""",
                    {
                        "t": "%.3fm %.3fm %.3fm"
                        % (mano["x"], mano["y"] + 0.02, mano["z"]),
                        "orbit": orbit,
                        "fov": "24deg",
                    },
                )
                time.sleep(0.2)
                viewer.screenshot(path=str(OUT / f"{nombre}_{vista}.png"))

        browser.close()

    (OUT / "_casos.json").write_text(json.dumps(casos, indent=2), "utf-8")
    print("\nCapturas en", OUT)


if __name__ == "__main__":
    main()
