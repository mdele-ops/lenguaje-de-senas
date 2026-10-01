"""Amplia trozos de la foto de referencia de la E para leer donde va cada dedo.

La foto viene desenfocada y pequena: sin recortar y escalar no se distingue si
el pulgar va tumbado cruzando la palma o de pie contra el indice.
"""
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "tools" / "screenshots" / "referencia" / "E_usuario3_mano.png"
OUT = ROOT / "tools" / "screenshots" / "zoom_e3"

# (nombre, izquierda, arriba, derecha, abajo) en fraccion de la imagen
TROZOS = {
    "1_yemas": (0.05, 0.05, 1.00, 0.45),
    "2_pulgar": (0.35, 0.40, 1.00, 0.85),
    "3_mitad": (0.05, 0.25, 1.00, 0.80),
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    img = Image.open(REF).convert("RGB")
    w, h = img.size
    print(f"referencia {w}x{h}")

    # rejilla sobre la foto completa para poder citar coordenadas
    rej = img.copy()
    d = ImageDraw.Draw(rej)
    for i in range(1, 10):
        x, y = w * i / 10, h * i / 10
        d.line([(x, 0), (x, h)], fill=(255, 0, 0), width=1)
        d.line([(0, y), (w, y)], fill=(0, 120, 255), width=1)
        d.text((x + 2, 2), f"{i/10:.1f}", fill=(255, 0, 0))
        d.text((2, y + 2), f"{i/10:.1f}", fill=(0, 120, 255))
    rej.resize((w * 2, h * 2), Image.LANCZOS).save(OUT / "_rejilla.png")

    for nombre, (a, b, c, e) in TROZOS.items():
        caja = (int(w * a), int(h * b), int(w * c), int(h * e))
        t = img.crop(caja)
        k = min(3.0, 900 / max(t.size))
        t.resize((int(t.width * k), int(t.height * k)), Image.LANCZOS).save(
            OUT / f"{nombre}.png"
        )
        print("trozo:", nombre, caja)


if __name__ == "__main__":
    main()
