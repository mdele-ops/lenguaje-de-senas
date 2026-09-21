"""Hoja de comparacion de la Q: lamina, version anterior, version nueva y trazo.

La primera fila responde a la forma y la segunda al movimiento: son los cuatro
extremos del circulo (arriba, derecha, abajo, izquierda) en el orden en que los
recorre la animacion, que es el sentido de las manecillas del reloj.
"""
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / "tools" / "screenshots"

CAJA = (150, 120, 480, 450)

FORMA = [
    ("Lamina del usuario", SHOTS / "zoom_captura" / "ref_Q_x8.png", None),
    ("Antes: G tumbada", SHOTS / "lab_q" / "00_actual.png", CAJA),
    ("Ahora: pico hacia abajo", SHOTS / "verify_q" / "Q_produccion.png", CAJA),
]
TRAZO = [
    ("1 arriba", SHOTS / "lab_q_mov" / "00.png", CAJA),
    ("2 derecha", SHOTS / "lab_q_mov" / "03.png", CAJA),
    ("3 abajo", SHOTS / "lab_q_mov" / "06.png", CAJA),
    ("4 izquierda", SHOTS / "lab_q_mov" / "09.png", CAJA),
]

CELL = 330
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
    cols = max(len(FORMA), len(TRAZO))
    hoja = Image.new("RGB", (CELL * cols, 2 * (CELL + LH)), (245, 245, 248))
    draw = ImageDraw.Draw(hoja)
    for fila, paneles in enumerate((FORMA, TRAZO)):
        for i, (titulo, path, caja) in enumerate(paneles):
            if not path.exists():
                print("falta:", path)
                continue
            x, y = i * CELL, fila * (CELL + LH)
            hoja.paste(recuadro(path, caja), (x, y))
            draw.rectangle([x, y + CELL, x + CELL, y + CELL + LH], fill=(20, 30, 50))
            draw.text((x + 8, y + CELL + 8), titulo, fill=(255, 255, 255))
    salida = SHOTS / "Q_antes_despues.png"
    hoja.save(salida)
    print("Hoja:", salida)


if __name__ == "__main__":
    main()
