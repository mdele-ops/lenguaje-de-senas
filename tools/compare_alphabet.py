"""Arma una hoja con la referencia y el render actual de cada letra, en pares,
para ver de un vistazo cuales no coinciden."""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "tools" / "screenshots" / "referencia"
REN = ROOT / "tools" / "screenshots" / "letters"
OUT = ROOT / "tools" / "screenshots"

ORDER = list("ABCDEFGHIJKLMN") + ["Ñ"] + list("OPQRSTUVWXYZ")
SAFE = {"Ñ": "N_"}


def build(pairs, out_path, cols=3, cell=270):
    label_h = 24
    rows = (len(pairs) + cols - 1) // cols
    pair_w = cell * 2
    sheet = Image.new("RGB", (cols * pair_w, rows * (cell + label_h)), (250, 250, 252))
    draw = ImageDraw.Draw(sheet)
    for i, (letra, ref, ren) in enumerate(pairs):
        x = (i % cols) * pair_w
        y = (i // cols) * (cell + label_h)
        sheet.paste(Image.open(ref).convert("RGB").resize((cell, cell), Image.LANCZOS), (x, y))
        sheet.paste(Image.open(ren).convert("RGB").resize((cell, cell), Image.LANCZOS), (x + cell, y))
        draw.rectangle([x, y + cell, x + pair_w, y + cell + label_h], fill=(20, 30, 50))
        draw.text((x + 8, y + cell + 7), f"{letra}   referencia | render", fill=(255, 255, 255))
        draw.line([x + cell, y, x + cell, y + cell], fill=(255, 90, 90), width=2)
    sheet.save(out_path)
    print("Comparacion:", out_path)


def main():
    view = sys.argv[1] if len(sys.argv) > 1 else "frente"
    letters = [a.upper() for a in sys.argv[2:]] or ORDER

    pairs = []
    for letra in letters:
        safe = SAFE.get(letra, letra)
        ref = REF / f"{safe}.png"
        ren = REN / f"{view}_{safe}.png"
        if ref.exists() and ren.exists():
            pairs.append((letra, ref, ren))

    if len(pairs) <= 9:
        build(pairs, OUT / f"_comparacion_{view}.png")
        return
    for i in range(0, len(pairs), 9):
        build(pairs[i : i + 9], OUT / f"_comparacion_{view}_{i // 9 + 1}.png")


if __name__ == "__main__":
    main()
