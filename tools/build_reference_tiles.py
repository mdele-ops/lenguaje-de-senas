"""Recorta la lamina del alfabeto LSM en un mosaico por letra, para poder
comparar cada seña renderizada contra su referencia."""
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "assets" / "Abecedario de lenguaje de señas.jpg"
OUT = ROOT / "tools" / "screenshots" / "referencia"

ROWS = [
    ["A", "B", "C", "D", "E"],
    ["F", "G", "H", "I", "J"],
    ["K", "L", "LL", "M", "N"],
    ["Ñ", "O", "P", "Q", "R"],
    ["RR", "S", "T", "U", "V"],
    ["W", "X", "Y", "Z"],
]

SAFE = {"Ñ": "N_"}


def main():
    img = Image.open(SRC).convert("RGB")
    w, h = img.size
    print("lamina:", w, h)
    OUT.mkdir(parents=True, exist_ok=True)

    # Fracciones medidas sobre la lamina original (5 columnas centradas,
    # 6 filas; la ultima fila tiene 4 y va corrida hacia el centro).
    left, right = 0.075, 0.945
    top, bottom = 0.085, 0.935
    col_w = (right - left) / 5
    row_h = (bottom - top) / 6

    for r, letters in enumerate(ROWS):
        offset = (5 - len(letters)) / 2 * col_w
        for c, letra in enumerate(letters):
            x0 = (left + offset + c * col_w) * w
            y0 = (top + r * row_h) * h
            tile = img.crop((int(x0), int(y0), int(x0 + col_w * w), int(y0 + row_h * h)))
            tile.save(OUT / f"{SAFE.get(letra, letra)}.png")

    # Hoja completa para verificar que los recortes quedaron alineados.
    cell = 150
    sheet = Image.new("RGB", (5 * cell, 6 * cell), (255, 255, 255))
    for r, letters in enumerate(ROWS):
        for c, letra in enumerate(letters):
            tile = Image.open(OUT / f"{SAFE.get(letra, letra)}.png").resize(
                (cell, cell), Image.LANCZOS
            )
            sheet.paste(tile, (c * cell, r * cell))
    sheet.save(OUT / "_verificacion.png")
    print("Recortes en", OUT)


if __name__ == "__main__":
    main()
