"""Banco de pruebas de la E contra la foto del usuario (E_usuario3).

`lab_e2` ya sabe encuadrar la mano y medirla; aqui va lo que le falta para
trabajar la pose: un constructor de poses con pocas perillas, un encuadre
cerrado (la hoja de `mira_e2` deja la mano del tamano de una moneda) y la foto
de referencia recortada a la mano y escalada al mismo alto que el render, para
poder comparar altura de yemas y sitio del pulgar de un vistazo.
"""
import json
from pathlib import Path

from PIL import Image, ImageDraw

from lab_e2 import MARCO_JS, aplicar, encuadrar, orbita, recorte

ROOT = Path(__file__).resolve().parents[1]
CAT = ROOT / "data" / "catalogo-lsm.json"
REF = ROOT / "tools" / "screenshots" / "referencia"

FINGERS = ("index", "middle", "ring", "pinky")
BONES = {
    "index": ("RightHandIndex1", "RightHandIndex2", "RightHandIndex3"),
    "middle": ("RightHandMiddle1", "RightHandMiddle2", "RightHandMiddle3"),
    "ring": ("RightHandRing1", "RightHandRing2", "RightHandRing3"),
    "pinky": ("RightHandPinky1", "RightHandPinky2", "RightHandPinky3"),
}
T1, T2, T3 = "RightHandThumb1", "RightHandThumb2", "RightHandThumb3"
MANO = "RightHand"

# Vistas mas cerradas que las de lab_e2: en la E lo que hay que juzgar es la
# altura de las yemas y donde cae el pulgar, y eso pide llenar el cuadro.
VISTAS = {
    "frente": (1.0, 0.0, 0.0),
    "pulgar": (0.55, 0.0, -0.84),
    "abajo": (0.80, -0.60, 0.0),
}
RADIO = 3.1
FOV = "22deg"


def catalogo():
    return json.loads(CAT.read_text("utf-8"))


def pose_catalogo(letra="E"):
    return next(x for x in catalogo()["senas"] if x["letra"] == letra)["pose"]


def cuatro(v):
    return tuple(v) if isinstance(v, (tuple, list)) else (v,) * 4


def pose_e(
    curl=0.92,
    mcp=14,
    pip=18,
    dip=8,
    spread=(-12, -4, 4, 12),
    tcurl=0.59,
    taside=-0.96,
    t1=(60, -35, 78),
    t2x=24,
    t3x=-11,
    mano=(-17.23, -4.999, -2.462),
    nudillos=None,
    largo=None,
):
    """Pose de la E con una perilla por grupo.

    `mcp`/`pip`/`dip` son los grados extra que se suman al curl en cada
    falange (el controlador los recorta al tope de la articulacion), y pueden
    ser un numero o una tupla indice/medio/anular/menique.
    """
    mcp, pip, dip = cuatro(mcp), cuatro(pip), cuatro(dip)
    spread = cuatro(spread)
    extra = {
        T1: {"x": t1[0], "y": t1[1], "z": t1[2]},
        T2: {"x": t2x},
        T3: {"x": t3x},
        MANO: {"x": mano[0], "y": mano[1], "z": mano[2]},
    }
    pose = {"thumb": {"curl": tcurl, "aside": taside}}
    for i, f in enumerate(FINGERS):
        b = BONES[f]
        extra[b[0]] = {"x": mcp[i]}
        extra[b[1]] = {"x": pip[i]}
        extra[b[2]] = {"x": dip[i]}
        pose[f] = {"curl": cuatro(curl)[i], "spread": spread[i]}
    pose["extra"] = extra
    if nudillos is not None:
        pose["nudillos"] = nudillos
    if largo is not None:
        pose["largo"] = largo
    return pose


def archivo(nombre):
    """Nombre de fichero seguro: las etiquetas llevan `/` y crearian carpetas."""
    return "".join(c if c.isalnum() or c in "-_+" else "_" for c in nombre)


def retratar(page, viewer, nombre, out, salida, vistas=VISTAS, radio=RADIO, fov=FOV):
    marco = page.evaluate(MARCO_JS)
    c = marco["centro"]
    t = "%.4fm %.4fm %.4fm" % (c["x"], c["y"], c["z"])
    for vista, pesos in vistas.items():
        encuadrar(page, orbita(marco, pesos, radio_palmas=radio), fov, t)
        salida.setdefault(vista, []).append(
            (nombre, recorte(page, viewer, out / f"{archivo(nombre)}_{vista}.png"))
        )


def ref_mano(cell):
    """Foto del usuario recortada a la mano y metida en un cuadro de `cell`."""
    img = Image.open(REF / "E_usuario3_mano.png").convert("RGB")
    k = cell / max(img.size)
    img = img.resize((int(img.width * k), int(img.height * k)), Image.LANCZOS)
    lienzo = Image.new("RGB", (cell, cell), (255, 255, 255))
    lienzo.paste(img, ((cell - img.width) // 2, (cell - img.height) // 2))
    return lienzo


def hoja(items, destino, cols=4, cell=420, con_ref=True):
    """Hoja de contactos; la primera casilla es la foto de referencia."""
    lh = 24
    celdas = []
    if con_ref:
        celdas.append(("FOTO usuario", ref_mano(cell)))
    for n, p in items:
        celdas.append((n, Image.open(p).convert("RGB").resize((cell, cell), Image.LANCZOS)))
    filas = (len(celdas) + cols - 1) // cols
    c = Image.new("RGB", (cols * cell, filas * (cell + lh)), (245, 245, 248))
    d = ImageDraw.Draw(c)
    for i, (n, im) in enumerate(celdas):
        x, y = (i % cols) * cell, (i // cols) * (cell + lh)
        c.paste(im, (x, y))
        d.rectangle([x, y + cell, x + cell, y + cell + lh], fill=(20, 30, 50))
        d.text((x + 6, y + cell + 7), n, fill=(255, 255, 255))
    c.save(destino)
    return destino


def publicar(salida, out, cols=4, cell=420):
    out.mkdir(parents=True, exist_ok=True)
    hechas = []
    for vista, imgs in salida.items():
        hechas.append(hoja(imgs, out / f"_{vista}.png", cols=cols, cell=cell,
                           con_ref=(vista == "frente")))
    return hechas


def probar(page, viewer, nombre, pose, out, salida, medir=None):
    aplicar(page, pose)
    m = page.evaluate(medir) if medir else None
    retratar(page, viewer, nombre, out, salida)
    return m
