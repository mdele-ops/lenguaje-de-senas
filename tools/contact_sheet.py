"""Junta las capturas de una carpeta en una sola hoja de contacto etiquetada.

Uso:
    py tools/contact_sheet.py CARPETA [COLUMNAS] [ANCHO_CELDA]
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / "tools" / "screenshots"

folder = SHOTS / sys.argv[1]
cols = int(sys.argv[2]) if len(sys.argv) > 2 else 5
cell_w = int(sys.argv[3]) if len(sys.argv) > 3 else 320

files = sorted(p for p in folder.glob("*.png") if p.name != "_hoja.png")
if not files:
    raise SystemExit(f"sin PNG en {folder}")

LABEL_H = 20
thumbs = []
for f in files:
    im = Image.open(f).convert("RGB")
    ratio = cell_w / im.width
    im = im.resize((cell_w, max(1, int(im.height * ratio))), Image.LANCZOS)
    thumbs.append((f.stem, im))

cell_h = max(im.height for _, im in thumbs) + LABEL_H
rows = (len(thumbs) + cols - 1) // cols
sheet = Image.new("RGB", (cols * cell_w, rows * cell_h), (18, 18, 24))
draw = ImageDraw.Draw(sheet)

for i, (name, im) in enumerate(thumbs):
    x = (i % cols) * cell_w
    y = (i // cols) * cell_h
    sheet.paste(im, (x, y + LABEL_H))
    draw.text((x + 5, y + 5), name, fill=(255, 235, 120))

out = folder / "_hoja.png"
sheet.save(out)
print(f"{len(thumbs)} imagenes -> {out}  ({sheet.width}x{sheet.height})")
