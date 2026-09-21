"""Genera un mapa de entorno de estudio cálido para model-viewer."""
import math
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "studio-env.jpg"


def blob(u, v, cx, cy, sx, sy):
    dx = (u - cx) / sx
    dy = (v - cy) / sy
    return math.exp(-0.5 * (dx * dx + dy * dy))


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    w, h = 1536, 768
    img = Image.new("RGB", (w, h))
    px = img.load()
    for y in range(h):
        v = y / (h - 1)
        for x in range(w):
            u = x / (w - 1)
            r = 252 - 38 * v
            g = 246 - 28 * v
            b = 238 - 8 * v + 22 * v
            key = blob(u, v, 0.36, 0.20, 0.16, 0.12)
            fill = blob(u, v, 0.70, 0.26, 0.20, 0.14) * 0.55
            rim = blob(u, v, 0.08, 0.32, 0.11, 0.16) * 0.38
            bounce = blob(u, v, 0.50, 0.82, 0.28, 0.12) * 0.22
            boost = key * 78 + fill * 44 + rim * 32 + bounce * 18
            px[x, y] = (
                min(255, int(r + boost)),
                min(255, int(g + boost * 0.93)),
                min(255, int(b + boost * 0.84)),
            )
    img.save(OUT, quality=92, optimize=True)
    print("OK", OUT, OUT.stat().st_size)


if __name__ == "__main__":
    main()
