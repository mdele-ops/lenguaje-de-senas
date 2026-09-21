"""Amplia la foto de referencia de la E para poder situar el pulgar.

En el tamano original (330x300 y 168x160) no se distingue donde acaba el pulgar
ni si las yemas se tocan entre si.
"""
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "tools" / "screenshots" / "referencia"
OUT = ROOT / "tools" / "screenshots" / "zoom_ref_e"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for nombre in ("E_usuario.png", "E_usuario2.png"):
        src = REF / nombre
        if not src.exists():
            continue
        img = Image.open(src).convert("RGB")
        base = src.stem
        escala = max(1, int(900 / max(img.size)))
        img.resize(
            (img.width * escala, img.height * escala), Image.LANCZOS
        ).save(OUT / f"{base}_x{escala}.png")
        print(nombre, img.size, "->", f"x{escala}")

        # mitad inferior derecha: ahi cae el pulgar en las dos fotos
        w, h = img.size
        rec = img.crop((int(w * 0.35), int(h * 0.25), w, int(h * 0.85)))
        rec.resize((rec.width * 4, rec.height * 4), Image.LANCZOS).save(
            OUT / f"{base}_pulgar.png"
        )
        # tercio superior: la fila de yemas
        rec2 = img.crop((0, 0, w, int(h * 0.45)))
        rec2.resize((rec2.width * 4, rec2.height * 4), Image.LANCZOS).save(
            OUT / f"{base}_yemas.png"
        )
    print("->", OUT)


if __name__ == "__main__":
    main()
