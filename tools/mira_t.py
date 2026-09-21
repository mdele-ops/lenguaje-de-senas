"""Recorte de la mano con el esqueleto dibujado DENTRO del recorte.

`enfoque_r.captura` recorta bien pero deja la imagen sin marcas, y
`overlay_e.dibujar_overlay` dibuja en coordenadas de pagina, que no son las del
recorte: si se juntan los dos, los huesos salen fuera. Como en la T todo se
decide en un bulto de veinte pixeles (que la yema del pulgar quede entre el
indice y el medio), hace falta lo uno con lo otro.

Aqui se proyectan los huesos a pixeles del propio visor, se recorta la captura
igual que en `enfoque_r`, y las marcas se pasan por la MISMA transformacion,
asi que caen donde tienen que caer.
"""
import time
from pathlib import Path

from PIL import Image, ImageDraw

from enfoque_r import CAJA_JS, MANO
from pose_lab_e import _GET_SCENE
import search_e9 as se9
from search_e9 import VISOR_CACHE

# Igual que CAJA_JS pero devolviendo el punto de cada hueso, no la caja.
PUNTOS_JS = (
    """
(nombres) => {
  const mv = document.getElementById('handViewer');
"""
    + _GET_SCENE
    + """
  const scene = getScene(mv);
  if (!scene) return { error: 'no-scene' };
  scene.updateMatrixWorld(true);
  const cam = scene.camera || (scene.getCamera && scene.getCamera());
  if (!cam) return { error: 'no-camera' };
  cam.updateMatrixWorld(true);
  if (cam.updateProjectionMatrix) cam.updateProjectionMatrix();
  const B = {};
  scene.traverse((o) => { if (o && o.name) B[o.name] = o; });
  const mul = (e, p) => ({
    x: e[0]*p.x + e[4]*p.y + e[8]*p.z + e[12]*p.w,
    y: e[1]*p.x + e[5]*p.y + e[9]*p.z + e[13]*p.w,
    z: e[2]*p.x + e[6]*p.y + e[10]*p.z + e[14]*p.w,
    w: e[3]*p.x + e[7]*p.y + e[11]*p.z + e[15]*p.w,
  });
  const vi = cam.matrixWorldInverse.elements;
  const pr = cam.projectionMatrix.elements;
  const rect = mv.getBoundingClientRect();
  const out = {};
  nombres.forEach((n) => {
    const b = B[n];
    if (!b) return;
    const e = b.matrixWorld.elements;
    const c = mul(pr, mul(vi, { x: e[12], y: e[13], z: e[14], w: 1 }));
    if (!c.w) return;
    out[n] = [
      (c.x / c.w * 0.5 + 0.5) * rect.width,
      (1 - (c.y / c.w * 0.5 + 0.5)) * rect.height,
    ];
  });
  return { pts: out, w: rect.width, h: rect.height };
}
"""
)

CADENAS = {
    "pulgar": ["mixamorig1RightHandThumb1_036", "mixamorig1RightHandThumb2_037",
               "mixamorig1RightHandThumb3_038", "mixamorig1RightHandThumb4_039"],
    "indice": ["mixamorig1RightHandIndex1_040", "mixamorig1RightHandIndex2_041",
               "mixamorig1RightHandIndex3_042", "mixamorig1RightHandIndex4_043"],
    "medio": ["mixamorig1RightHandMiddle1_044", "mixamorig1RightHandMiddle2_045",
              "mixamorig1RightHandMiddle3_046", "mixamorig1RightHandMiddle4_047"],
    "anular": ["mixamorig1RightHandRing1_048", "mixamorig1RightHandRing2_049",
               "mixamorig1RightHandRing3_050", "mixamorig1RightHandRing4_051"],
    "menique": ["mixamorig1RightHandPinky1_052", "mixamorig1RightHandPinky2_053",
                "mixamorig1RightHandPinky3_054", "mixamorig1RightHandPinky4_055"],
}
COLORES = {
    "pulgar": (235, 30, 30),
    "indice": (40, 130, 245),
    "medio": (40, 200, 80),
    "anular": (255, 150, 20),
    "menique": (190, 110, 235),
}
TODOS = [n for cad in CADENAS.values() for n in cad]


def abrir_nitido(p, lado=760, escala=2):
    """Como `search_e9.abrir` pero dibujando la pagina a mas resolucion.

    El visor de la pagina mide unos 860x420 CSS y la mano ocupa poco mas de
    300 px de eso: cualquier recorte acaba siendo una ampliacion borrosa, y en
    la T todo se decide en un bulto pequeño (si la yema del pulgar asoma o no
    entre indice y medio). Con `device_scale_factor` el navegador dibuja el
    mismo encuadre con mas pixeles, asi que el recorte sale nitido sin tocar la
    pagina ni la camara.

    Ojo con pasarse: el WebGL de estas pruebas va por software (swiftshader) y
    el coste crece con el area. A 1000 px por escala 3 (o sea 3000x3000) cada
    cuadro tarda minutos y el script se queda colgado; 760 por 2 va fino.
    """
    browser = p.chromium.launch(
        channel="chrome",
        args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"],
    )
    contexto = browser.new_context(
        viewport={"width": lado, "height": lado}, device_scale_factor=escala
    )
    page = contexto.new_page()
    if VISOR_CACHE.exists():
        page.route(
            "**/@google/model-viewer*/**",
            lambda ruta: ruta.fulfill(
                path=str(VISOR_CACHE), content_type="application/javascript"
            ),
        )
    page.goto(se9.URL, wait_until="networkidle", timeout=60000)
    page.wait_for_selector("#anim-info", timeout=20000, state="attached")
    for _ in range(150):
        if page.evaluate(
            "() => !!(window.__LSM_CONTROLLER__ "
            "&& window.__LSM_CONTROLLER__.isModelReady())"
        ):
            break
        time.sleep(0.4)
    else:
        estado = page.inner_text("#anim-info").strip()[:200]
        browser.close()
        raise RuntimeError("El modelo 3D no cargo. Estado: " + estado)
    time.sleep(1.5)
    return browser, page


def visor_cuadrado(page, lado=1000):
    """Deja `#handViewer` cuadrado y grande antes de capturar.

    En la pagina el visor es un rectangulo ancho y bajo, asi que la mano cae
    arriba y ocupa pocos pixeles: el recorte acaba siendo una ampliacion y no
    se distingue el pulgar del indice. Cuadrado y a 1000 px la mano sale con
    pixeles de verdad.
    """
    page.evaluate(
        """(lado) => {
            const mv = document.getElementById('handViewer');
            mv.style.width = lado + 'px';
            mv.style.height = lado + 'px';
            mv.style.maxWidth = 'none';
            window.dispatchEvent(new Event('resize'));
        }""",
        lado,
    )
    time.sleep(0.5)


def acerca(page, hand, orbit, fov="24deg"):
    """Camara pegada a la mano, apuntando al centro que da HAND_POS_JS."""
    page.evaluate(
        """(a) => {
            const mv = document.getElementById('handViewer');
            mv.cameraTarget = a.t;
            mv.cameraOrbit = a.orbit;
            mv.fieldOfView = a.fov;
            mv.jumpCameraToGoal();
        }""",
        {
            "t": "%.3fm %.3fm %.3fm" % (hand["x"], hand["y"], hand["z"]),
            "orbit": orbit,
            "fov": fov,
        },
    )
    time.sleep(0.25)


def captura(page, ruta, esqueleto=False, margen=0.28, lado=560, huesos=MANO):
    """Recorte cuadrado centrado en la mano, opcionalmente con el esqueleto."""
    page.evaluate(
        "() => new Promise((r) => requestAnimationFrame("
        "() => requestAnimationFrame(r)))"
    )
    caja = page.evaluate(CAJA_JS, huesos)
    datos = page.evaluate(PUNTOS_JS, TODOS) if esqueleto else None
    visor = page.query_selector("#handViewer")
    visor.screenshot(path=str(ruta))
    if caja.get("error"):
        return caja

    im = Image.open(ruta).convert("RGB")
    ex, ey = im.width / caja["w"], im.height / caja["h"]

    if datos and not datos.get("error"):
        d = ImageDraw.Draw(im)
        for dedo, cadena in CADENAS.items():
            col = COLORES[dedo]
            seq = [
                (datos["pts"][n][0] * ex, datos["pts"][n][1] * ey)
                for n in cadena
                if n in datos["pts"]
            ]
            if len(seq) > 1:
                d.line(seq, fill=col, width=2)
            for i, pt in enumerate(seq):
                r = 6 if (dedo == "pulgar" and i == len(seq) - 1) else 3
                d.ellipse([pt[0]-r, pt[1]-r, pt[0]+r, pt[1]+r], fill=col)

    cx = (caja["x0"] + caja["x1"]) / 2 * ex
    cy = (caja["y0"] + caja["y1"]) / 2 * ey
    r = max((caja["x1"] - caja["x0"]) * ex, (caja["y1"] - caja["y0"]) * ey) / 2
    r = max(r * (1 + margen), 40)

    lienzo = Image.new("RGB", (int(2 * r), int(2 * r)), (8, 12, 24))
    lienzo.paste(im, (int(r - cx), int(r - cy)))
    lienzo.resize((lado, lado), Image.LANCZOS).save(ruta)
    return caja
