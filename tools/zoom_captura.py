"""Amplia una captura de pantalla para poder mirar el pulgar de cerca.

Uso: py tools/zoom_captura.py <ruta> [nombre]
"""
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "zoom_captura"


def main():
    src = Path(sys.argv[1])
    nombre = sys.argv[2] if len(sys.argv) > 2 else src.stem[:24]
    OUT.mkdir(parents=True, exist_ok=True)

    img = Image.open(src).convert("RGB")
    escala = max(1, int(1000 / max(img.size)))
    img.resize((img.width * escala, img.height * escala), Image.LANCZOS).save(
        OUT / f"{nombre}_x{escala}.png"
    )
    print(src.name, img.size, "->", f"x{escala}")

    # la mano ocupa el tercio superior izquierdo de la captura de la app
    w, h = img.size
    rec = img.crop((0, 0, int(w * 0.62), int(h * 0.78)))
    rec.resize((rec.width * escala * 2, rec.height * escala * 2), Image.LANCZOS).save(
        OUT / f"{nombre}_mano.png"
    )
    print("->", OUT)


if __name__ == "__main__":
    main()
