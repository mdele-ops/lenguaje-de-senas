"""Amplia la casilla de la H (y de la G, su vecina) de la lamina de referencia."""
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "tools" / "screenshots" / "referencia"
OUT = ROOT / "tools" / "screenshots" / "ref_h"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for letra in ("H", "G", "U"):
        img = Image.open(REF / f"{letra}.png").convert("RGB")
        k = 5
        img.resize((img.width * k, img.height * k), Image.LANCZOS).save(
            OUT / f"{letra}_big.png"
        )
        print(letra, img.size, "->", (img.width * k, img.height * k))


if __name__ == "__main__":
    main()
