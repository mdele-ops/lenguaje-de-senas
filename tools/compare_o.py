"""Pone la foto de referencia de la O junto a los renders para compararlas.

Uso:
    py tools/compare_o.py CARPETA [nombre1 nombre2 ...]
Si no se pasan nombres, usa todos los PNG de la carpeta.
"""
import os
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / "tools" / "screenshots"
REF = SHOTS / "reference_o" / "ref_O_mano_x5.png"

# Recorte donde cae la mano en los renders del #viewer (883x421).
# Se puede cambiar con la variable de entorno HAND_BOX="x0,y0,x1,y1".
HAND_BOX = tuple(
    int(v) for v in os.environ.get("HAND_BOX", "235,25,475,345").split(",")
)
CELL_H = 560
LABEL_H = 22


def cell(img, label):
    ratio = CELL_H / img.height
    img = img.resize((max(1, int(img.width * ratio)), CELL_H), Image.LANCZOS)
    out = Image.new("RGB", (img.width, CELL_H + LABEL_H), (18, 18, 24))
    out.paste(img, (0, LABEL_H))
    ImageDraw.Draw(out).text((5, 5), label, fill=(255, 235, 120))
    return out


def main():
    folder = SHOTS / sys.argv[1]
    names = sys.argv[2:]
    files = (
        [folder / f"{n}.png" for n in names]
        if names
        else sorted(p for p in folder.glob("*.png") if not p.name.startswith("_"))
    )

    cells = [cell(Image.open(REF).convert("RGB"), "REFERENCIA")]
    for f in files:
        im = Image.open(f).convert("RGB").crop(HAND_BOX)
        cells.append(cell(im, f.stem))

    w = sum(c.width for c in cells)
    h = max(c.height for c in cells)
    sheet = Image.new("RGB", (w, h), (18, 18, 24))
    x = 0
    for c in cells:
        sheet.paste(c, (x, 0))
        x += c.width

    out = folder / "_vs_referencia.png"
    sheet.save(out)
    print(f"{len(files)} renders vs referencia -> {out} ({sheet.width}x{sheet.height})")


if __name__ == "__main__":
    main()
