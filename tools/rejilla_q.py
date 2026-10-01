"""Rejilla sobre la lamina de la Q para leer los angulos de la mano y del arco.

Igual que se hizo con la P: la lamina llega a 85x114 px, asi que se amplia y se
le dibuja encima una cuadricula numerada. Con las coordenadas leidas a ojo se
calculan los angulos en pantalla (0 = a la derecha, 90 = hacia arriba), que son
los que despues se le piden al esqueleto.

Uso: py tools/rejilla_q.py [x1,y1 x2,y2 ...]  -> imprime el angulo de cada par.
"""
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "tools" / "screenshots" / "ref_Q.png"
OUT = ROOT / "tools" / "screenshots" / "ref_Q_rejilla.png"
ESCALA = 8
PASO = 40


def angulo(a, b):
    # la imagen crece hacia abajo; en pantalla el eje y crece hacia arriba
    return math.degrees(math.atan2(-(b[1] - a[1]), b[0] - a[0]))


def main():
    if len(sys.argv) > 1:
        pts = [tuple(int(v) for v in p.split(",")) for p in sys.argv[1:]]
        for a, b in zip(pts, pts[1:]):
            print(f"{a} -> {b}: {angulo(a, b):+7.1f}")
        return

    img = Image.open(SRC).convert("RGB")
    big = img.resize((img.width * ESCALA, img.height * ESCALA), Image.LANCZOS)
    draw = ImageDraw.Draw(big)
    for x in range(0, big.width, PASO):
        fuerte = x % (PASO * 5) == 0
        draw.line([(x, 0), (x, big.height)], fill=(0, 150, 255) if fuerte else (200, 220, 235))
        if fuerte:
            draw.text((x + 3, 3), str(x), fill=(0, 90, 160))
    for y in range(0, big.height, PASO):
        fuerte = y % (PASO * 5) == 0
        draw.line([(0, y), (big.width, y)], fill=(0, 150, 255) if fuerte else (200, 220, 235))
        if fuerte:
            draw.text((3, y + 3), str(y), fill=(0, 90, 160))
    big.save(OUT)
    print("Rejilla:", OUT, big.size)


if __name__ == "__main__":
    main()
