"""Busqueda de la E: dedos separados (que no se atraviesen) y pulgar recogido.

Se puntua sobre la geometria del esqueleto, no sobre el render, porque el
sombreado del avatar hace muy dificil juzgar a ojo si dos dedos se solapan.

Metricas (todas normalizadas al largo de la palma muneca->nudillo del indice):
  sepMin    separacion entre yemas vecinas. Por debajo de ~0.16 los dedos se
            atraviesan; los nudillos estan a ~0.23, asi que ese es el techo.
  foldMin   cuanto baja la yema respecto a su nudillo: la E dobla los dedos
            hasta dejar las yemas claramente por debajo.
  frontMin  la yema queda por delante de la palma (apoyada sobre el pulgar).
  across    posicion de la punta del pulgar entre el indice (0) y el
            menique (1). En la letra el pulgar se queda corto: ~0.2-0.4.
  tipoI     distancia punta del pulgar -> yema del indice, para que se toquen.
"""
import itertools
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from pose_lab_e import ARM, BONES, FINGERS, T1, T2, T3, _GET_SCENE

ROOT = Path(__file__).resolve().parents[1]
URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=e9"

FAN = (-1.5, -0.5, 0.5, 1.5)

MEASURE_JS = (
    """
() => {
  const mv = document.getElementById('handViewer');
"""
    + _GET_SCENE
    + """
  const scene = getScene(mv);
  if (!scene) return { error: 'no-scene' };
  if (scene.updateMatrixWorld) scene.updateMatrixWorld(true);
  const B = {};
  scene.traverse((o) => { if (o && o.name) B[o.name] = o; });
  const P = (n) => {
    const b = B[n];
    if (!b || !b.matrixWorld) return null;
    const e = b.matrixWorld.elements;
    return { x: e[12], y: e[13], z: e[14] };
  };
  const d = (a, b) => Math.hypot(a.x-b.x, a.y-b.y, a.z-b.z);

  const wrist = P('mixamorig1RightHand_035');
  const tip = {
    I: P('mixamorig1RightHandIndex4_043'), M: P('mixamorig1RightHandMiddle4_047'),
    R: P('mixamorig1RightHandRing4_051'),  P: P('mixamorig1RightHandPinky4_055'),
  };
  const dip = {
    I: P('mixamorig1RightHandIndex3_042'), M: P('mixamorig1RightHandMiddle3_046'),
    R: P('mixamorig1RightHandRing3_050'),  P: P('mixamorig1RightHandPinky3_054'),
  };
  const pip = {
    I: P('mixamorig1RightHandIndex2_041'), M: P('mixamorig1RightHandMiddle2_045'),
    R: P('mixamorig1RightHandRing2_049'),  P: P('mixamorig1RightHandPinky2_053'),
  };
  const knu = {
    I: P('mixamorig1RightHandIndex1_040'), M: P('mixamorig1RightHandMiddle1_044'),
    R: P('mixamorig1RightHandRing1_048'),  P: P('mixamorig1RightHandPinky1_052'),
  };
  const t2 = P('mixamorig1RightHandThumb2_037');
  const t3 = P('mixamorig1RightHandThumb3_038');
  const t4 = P('mixamorig1RightHandThumb4_039');
  const palm = d(wrist, knu.I) || 1;
  const o = { palm: palm };

  const pares = [['I','M'], ['M','R'], ['R','P']];
  let sepMin = 9, sepTipMin = 9;
  pares.forEach(([a, b]) => {
    // se comparan las tres articulaciones de cada dedo: el solape puede
    // aparecer en la falange media aunque las yemas queden separadas
    const s = Math.min(d(tip[a], tip[b]), d(dip[a], dip[b]), d(pip[a], pip[b])) / palm;
    sepMin = Math.min(sepMin, s);
    sepTipMin = Math.min(sepTipMin, d(tip[a], tip[b]) / palm);
  });
  o.sepMin = sepMin;
  o.sepTipMin = sepTipMin;
  o.knuSep = Math.min(d(knu.I, knu.M), d(knu.M, knu.R), d(knu.R, knu.P)) / palm;

  let foldMin = 9, frontMin = 9;
  ['I','M','R','P'].forEach((k) => {
    foldMin = Math.min(foldMin, (knu[k].y - tip[k].y) / palm);
    frontMin = Math.min(frontMin, (tip[k].z - knu[k].z) / palm);
  });
  o.foldMin = foldMin;
  o.frontMin = frontMin;

  // eje transversal de la palma: del nudillo del indice al del menique
  const ax = { x: knu.P.x-knu.I.x, y: knu.P.y-knu.I.y, z: knu.P.z-knu.I.z };
  const alen2 = ax.x*ax.x + ax.y*ax.y + ax.z*ax.z || 1;
  const proj = (p) => ((p.x-knu.I.x)*ax.x + (p.y-knu.I.y)*ax.y + (p.z-knu.I.z)*ax.z) / alen2;
  o.across = proj(t4);
  o.acrossT3 = proj(t3);
  o.thumbLen = d(t2, t4) / palm;
  o.tipoI = d(t4, tip.I) / palm;
  o.tipoM = d(t4, tip.M) / palm;
  // el pulgar va por delante de la palma y las yemas se apoyan encima
  o.thumbFront = (t4.z - knu.I.z) / palm;
  o.thumbUnderTips = (tip.I.y - t4.y) / palm;
  return o;
}
"""
)


def pose_e(mcp, pip, dip, conv, tcurl, taside, t1y, t1z, t2x, t3x, arm_z=-18):
    def four(v):
        return v if isinstance(v, (tuple, list)) else (v,) * 4

    mcp, pip, dip = four(mcp), four(pip), four(dip)
    extra = {ARM: {"z": arm_z}, T1: {"y": t1y, "z": t1z}}
    for i, f in enumerate(FINGERS):
        b = BONES[f]
        extra[b[0]] = {"x": mcp[i]}
        extra[b[1]] = {"x": pip[i]}
        if dip[i]:
            extra[b[2]] = {"x": dip[i]}
    if t2x:
        extra[T2] = {"x": t2x}
    if t3x:
        extra[T3] = {"x": t3x}
    pose = {"thumb": {"curl": tcurl, "aside": taside}, "extra": extra}
    for i, f in enumerate(FINGERS):
        pose[f] = {"curl": 0.0, "spread": FAN[i] * conv}
    return pose


def banda(v, lo, hi):
    """0 dentro de [lo, hi]; crece linealmente al alejarse."""
    if v < lo:
        return lo - v
    if v > hi:
        return v - hi
    return 0.0


def puntuar(m):
    """Menor es mejor. Los pesos reflejan lo que se ve en pantalla."""
    p = 0.0
    # que no se atraviesen: es el defecto principal que reporto el usuario
    p += 6.0 * banda(m["sepMin"], 0.17, 0.26)
    p += 3.0 * banda(m["sepTipMin"], 0.18, 0.30)
    # dedos bien doblados y apoyados por delante
    p += 2.5 * banda(m["foldMin"], 0.45, 1.10)
    p += 2.0 * banda(m["frontMin"], 0.10, 0.80)
    # pulgar corto y recogido del lado del indice
    p += 5.0 * banda(m["across"], 0.10, 0.42)
    p += 2.0 * banda(m["thumbLen"], 0.18, 0.42)
    p += 2.0 * banda(m["tipoI"], 0.10, 0.42)
    p += 1.5 * banda(m["thumbFront"], 0.15, 0.75)
    # las yemas quedan por encima del pulgar, no al reves
    p += 1.5 * banda(m["thumbUnderTips"], -0.10, 0.60)
    return p


VISOR_CACHE = Path(__file__).resolve().parent / "vendor" / "model-viewer.min.js"


def abrir(p):
    browser = p.chromium.launch(
        channel="chrome",
        args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"],
    )
    page = browser.new_page(viewport={"width": 500, "height": 500})
    if VISOR_CACHE.exists():
        # practica.html baja model-viewer de unpkg y la descarga falla a menudo;
        # cada fallo cuesta mas de un minuto de espera. Para las pruebas se
        # sirve la copia local sin tocar la pagina.
        page.route(
            "**/@google/model-viewer*/**",
            lambda ruta: ruta.fulfill(
                path=str(VISOR_CACHE), content_type="application/javascript"
            ),
        )
    page.goto(URL, wait_until="networkidle", timeout=60000)
    page.wait_for_selector("#anim-info", timeout=20000, state="attached")
    listo = False
    for _ in range(150):
        if page.evaluate(
            "() => !!(window.__LSM_CONTROLLER__ && window.__LSM_CONTROLLER__.isModelReady())"
        ):
            listo = True
            break
        time.sleep(0.4)
    if not listo:
        # sin esto los huesos salen null y el error aparece mucho despues,
        # dentro del JS de medida, con un mensaje que no dice nada
        estado = page.inner_text("#anim-info").strip()[:200]
        browser.close()
        raise RuntimeError("El modelo 3D no cargo. Estado: " + estado)
    time.sleep(1.5)
    return browser, page


def evaluar(page, pose):
    page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
    return page.evaluate(MEASURE_JS)


def linea(nombre, m, score):
    return (
        f"{nombre:34s} score={score:6.3f} sep={m['sepMin']:.3f}/{m['sepTipMin']:.3f} "
        f"fold={m['foldMin']:.2f} front={m['frontMin']:+.2f} "
        f"across={m['across']:+.2f} tLen={m['thumbLen']:.2f} tipoI={m['tipoI']:.2f}"
    )


def main():
    catalogo = json.loads((ROOT / "data" / "catalogo-lsm.json").read_text("utf-8"))
    actual = next(s for s in catalogo["senas"] if s["letra"] == "E")["pose"]

    with sync_playwright() as p:
        browser, page = abrir(p)

        m = evaluar(page, actual)
        print("REFERENCIA (catalogo actual)")
        print(" ", linea("E_catalogo", m, puntuar(m)))
        print(f"  nudillos separados: {m['knuSep']:.3f}  -> techo realista de sepMin")
        print()

        # ---- Fase 1: forma de los cuatro dedos -------------------------------
        base_thumb = dict(tcurl=0.6, taside=-0.5, t1y=-60, t1z=10, t2x=60, t3x=0)
        rejilla1 = list(
            itertools.product(
                (40, 55, 70, 85),  # mcp
                (70, 85, 100),  # pip
                (0, 15, 30),  # dip
                (0, 3, 6, 9),  # conv
            )
        )
        print(f"Fase 1: {len(rejilla1)} combinaciones de dedos")
        r1 = []
        for mcp, pip, dip, conv in rejilla1:
            pose = pose_e(mcp, pip, dip, conv, **base_thumb)
            mm = evaluar(page, pose)
            # en esta fase solo importan los dedos
            s = (
                6.0 * banda(mm["sepMin"], 0.17, 0.26)
                + 3.0 * banda(mm["sepTipMin"], 0.18, 0.30)
                + 2.5 * banda(mm["foldMin"], 0.45, 1.10)
                + 2.0 * banda(mm["frontMin"], 0.10, 0.80)
            )
            r1.append((s, (mcp, pip, dip, conv), mm))
        r1.sort(key=lambda t: t[0])
        for s, k, mm in r1[:8]:
            print(" ", linea(f"mcp{k[0]} pip{k[1]} dip{k[2]} conv{k[3]}", mm, s))
        print()

        mejores_dedos = [k for _, k, _ in r1[:3]]

        # ---- Fase 2: pulgar --------------------------------------------------
        rejilla2 = list(
            itertools.product(
                (0.4, 0.6, 0.8),  # tcurl
                (-45, -60, -75),  # t1y
                (0, 15, 30),  # t1z
                (40, 60, 80),  # t2x
                (0, 25, 50),  # t3x
            )
        )
        print(f"Fase 2: {len(rejilla2)} combinaciones de pulgar x {len(mejores_dedos)} dedos")
        r2 = []
        for dedos in mejores_dedos:
            mcp, pip, dip, conv = dedos
            for tcurl, t1y, t1z, t2x, t3x in rejilla2:
                pose = pose_e(
                    mcp, pip, dip, conv,
                    tcurl=tcurl, taside=-0.5, t1y=t1y, t1z=t1z, t2x=t2x, t3x=t3x,
                )
                mm = evaluar(page, pose)
                r2.append((puntuar(mm), (dedos, (tcurl, t1y, t1z, t2x, t3x)), mm))
        r2.sort(key=lambda t: t[0])
        print("MEJORES COMBINADAS")
        for s, k, mm in r2[:12]:
            dedos, th = k
            nombre = (
                f"mcp{dedos[0]} pip{dedos[1]} dip{dedos[2]} c{dedos[3]} | "
                f"tc{th[0]} y{th[1]} z{th[2]} t2{th[3]} t3{th[4]}"
            )
            print(" ", linea(nombre, mm, s))

        browser.close()

    salida = ROOT / "tools" / "screenshots" / "search_e9.json"
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text(
        json.dumps(
            [
                {"score": s, "dedos": k[0], "pulgar": k[1], "metricas": mm}
                for s, k, mm in r2[:30]
            ],
            indent=2,
        ),
        "utf-8",
    )
    print("\nTop 30 ->", salida)


if __name__ == "__main__":
    main()
