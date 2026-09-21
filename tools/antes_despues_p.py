"""Hoja de comparacion de la P: referencias del usuario contra el resultado."""
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / "tools" / "screenshots"

# Los dos ultimos van recortados de la captura de produccion (la camara real
# de practica.html), para comparar lo que de verdad ve el usuario.
CAJA = (215, 65, 415, 265)

PANELES = [
    ("Foto del usuario", SHOTS / "ref_P_zoom.png", None),
    ("1: de tres cuartos", SHOTS / "lab_p7" / "00_actual45.png", CAJA),
    ("2: de perfil, tiesa", SHOTS / "lab_p8" / "J_arm-30.png", CAJA),
    ("3: de perfil y doblada", SHOTS / "lab_p_final" / "P_produccion.png", CAJA),
]

CELL = 360
LH = 26


def recuadro(path, caja=None):
    im = Image.open(path).convert("RGB")
    if caja:
        im = im.crop(caja)
    lado = min(im.size)
    return im.crop(
        (
            (im.width - lado) // 2,
            (im.height - lado) // 2,
            (im.width + lado) // 2,
            (im.height + lado) // 2,
        )
    ).resize((CELL, CELL), Image.LANCZOS)


def main():
    hoja = Image.new("RGB", (CELL * len(PANELES), CELL + LH), (245, 245, 248))
    draw = ImageDraw.Draw(hoja)
    for i, (titulo, path, caja) in enumerate(PANELES):
        if not path.exists():
            print("falta:", path)
            continue
        hoja.paste(recuadro(path, caja), (i * CELL, 0))
        draw.rectangle(
            [i * CELL, CELL, (i + 1) * CELL, CELL + LH], fill=(20, 30, 50)
        )
        draw.text((i * CELL + 8, CELL + 8), titulo, fill=(255, 255, 255))
    salida = SHOTS / "P_antes_despues.png"
    hoja.save(salida)
    print("Hoja:", salida)


if __name__ == "__main__":
    main()
