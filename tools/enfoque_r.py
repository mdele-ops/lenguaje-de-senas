"""Recorte exacto alrededor de la mano, proyectando los huesos a la pantalla.

Apuntar `cameraTarget` a mano nunca deja el encuadre donde uno quiere: el visor
mueve el modelo y el elemento no es cuadrado, asi que la mano acaba en una
esquina y a distinta escala en cada captura. Comparar candidatas asi es
imposible.

Aqui la camara se deja quieta y se hace al reves: se proyectan los huesos de la
mano con la matriz de la camara, se saca su caja en pixeles y se recorta la
captura sobre esa caja. El resultado es que la mano sale siempre centrada y del
mismo tamano, que es lo unico que permite poner dos poses una al lado de otra.
"""
from pathlib import Path

from PIL import Image, ImageDraw

from pose_lab_e import _GET_SCENE

# Proyecta los huesos pedidos a pixeles del propio <model-viewer>.
CAJA_JS = (
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

  // multiplicacion punto x matriz4 (three guarda las columnas seguidas)
  const mul = (e, p) => ({
    x: e[0]*p.x + e[4]*p.y + e[8]*p.z + e[12]*p.w,
    y: e[1]*p.x + e[5]*p.y + e[9]*p.z + e[13]*p.w,
    z: e[2]*p.x + e[6]*p.y + e[10]*p.z + e[14]*p.w,
    w: e[3]*p.x + e[7]*p.y + e[11]*p.z + e[15]*p.w,
  });

  const vi = cam.matrixWorldInverse.elements;
  const pr = cam.projectionMatrix.elements;
  const rect = mv.getBoundingClientRect();

  let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9, n = 0;
  nombres.forEach((nombre) => {
    const b = B[nombre];
    if (!b) return;
    const e = b.matrixWorld.elements;
    const mundo = { x: e[12], y: e[13], z: e[14], w: 1 };
    const clip = mul(pr, mul(vi, mundo));
    if (!clip.w) return;
    const px = (clip.x / clip.w * 0.5 + 0.5) * rect.width;
    const py = (1 - (clip.y / clip.w * 0.5 + 0.5)) * rect.height;
    x0 = Math.min(x0, px); x1 = Math.max(x1, px);
    y0 = Math.min(y0, py); y1 = Math.max(y1, py);
    n++;
  });
  if (!n) return { error: 'sin-huesos' };
  return { x0, y0, x1, y1, w: rect.width, h: rect.height };
}
"""
)

MANO = [
    "mixamorig1RightHand_035",
    "mixamorig1RightHandIndex1_040", "mixamorig1RightHandIndex4_043",
    "mixamorig1RightHandMiddle1_044", "mixamorig1RightHandMiddle4_047",
    "mixamorig1RightHandRing1_048", "mixamorig1RightHandRing4_051",
    "mixamorig1RightHandPinky1_052", "mixamorig1RightHandPinky4_055",
    "mixamorig1RightHandThumb1_036", "mixamorig1RightHandThumb4_039",
]
DEDOS = [
    "mixamorig1RightHandIndex1_040", "mixamorig1RightHandIndex2_041",
    "mixamorig1RightHandIndex3_042", "mixamorig1RightHandIndex4_043",
    "mixamorig1RightHandMiddle1_044", "mixamorig1RightHandMiddle2_045",
    "mixamorig1RightHandMiddle3_046", "mixamorig1RightHandMiddle4_047",
]


def captura(page, ruta, huesos=MANO, margen=0.35, lado=520):
    """Guarda un recorte cuadrado centrado en `huesos`, siempre a la misma escala."""
    # el visor actualiza las matrices de la camara al pintar: sin esperar un
    # par de frames la caja sale calculada con la camara ANTERIOR y el recorte
    # aparece desplazado
    page.evaluate(
        "() => new Promise((r) => requestAnimationFrame("
        "() => requestAnimationFrame(r)))"
    )
    caja = page.evaluate(CAJA_JS, huesos)
    visor = page.query_selector("#handViewer")
    visor.screenshot(path=str(ruta))
    if caja.get("error"):
        return caja

    im = Image.open(ruta).convert("RGB")
    # la caja viene en pixeles CSS y la captura puede tener otra densidad
    ex, ey = im.width / caja["w"], im.height / caja["h"]
    cx = (caja["x0"] + caja["x1"]) / 2 * ex
    cy = (caja["y0"] + caja["y1"]) / 2 * ey
    r = max((caja["x1"] - caja["x0"]) * ex, (caja["y1"] - caja["y0"]) * ey) / 2
    r = max(r * (1 + margen), 40)

    # fondo por si el recorte se sale del elemento
    lienzo = Image.new("RGB", (int(2 * r), int(2 * r)), (8, 12, 24))
    lienzo.paste(im, (int(r - cx), int(r - cy)))
    lienzo.resize((lado, lado), Image.LANCZOS).save(ruta)
    return caja


def hoja(items, out_path, cols=4, cell=340, titulo=None):
    lh = 26
    top = 30 if titulo else 0
    filas = (len(items) + cols - 1) // cols
    canvas = Image.new(
        "RGB", (cols * cell, top + filas * (cell + lh)), (245, 245, 248)
    )
    draw = ImageDraw.Draw(canvas)
    if titulo:
        draw.text((8, 9), titulo, fill=(20, 20, 30))
    for i, (name, path) in enumerate(items):
        x, y = (i % cols) * cell, top + (i // cols) * (cell + lh)
        im = Image.open(path).convert("RGB")
        lado = min(im.size)
        im = im.crop(
            (
                (im.width - lado) // 2, (im.height - lado) // 2,
                (im.width + lado) // 2, (im.height + lado) // 2,
            )
        )
        canvas.paste(im.resize((cell, cell), Image.LANCZOS), (x, y))
        draw.rectangle([x, y + cell, x + cell, y + cell + lh], fill=(20, 30, 50))
        draw.text((x + 6, y + cell + 8), name, fill=(255, 255, 255))
    canvas.save(out_path)
    print("Hoja:", out_path)
    return out_path
