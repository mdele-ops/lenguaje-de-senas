"""Amplia la lamina de la T del usuario para poder leer donde va cada dedo.

La lamina llega a 194x254 y con la mano ocupando poco mas de un tercio: a ese
tamano no se distingue si el pulgar asoma ENTRE el indice y el medio (T) o si
cruza por delante de los dos (S). Aqui se recorta la mano y se sube a 900 px,
que es donde esa diferencia ya se ve.
"""
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
LAMINA = ROOT / "tools" / "screenshots" / "lamina_T.png"
OUT = ROOT / "tools" / "screenshots" / "zoom_t"
OUT.mkdir(parents=True, exist_ok=True)

# Caja de la mano dentro de la lamina (medida a ojo sobre los 194x254).
MANO = (46, 30, 152, 168)


def guarda(im, ruta, lado):
    im.resize((lado, int(lado * im.height / im.width)), Image.LANCZOS).save(ruta)
    print(" ", ruta.name, im.size, "->", lado)


def main():
    lam = Image.open(LAMINA).convert("RGB")
    guarda(lam, OUT / "_lamina.png", 600)

    mano = lam.crop(MANO)
    guarda(mano, OUT / "_mano.png", 900)

    # Mitad de arriba: es donde asoma el pulgar y donde se decide la letra.
    arriba = mano.crop((0, 0, mano.width, int(mano.height * 0.55)))
    guarda(arriba, OUT / "_arriba.png", 900)

    # Rejilla de tercios sobre la mano, para poder hablar de posiciones.
    rej = mano.resize((900, int(900 * mano.height / mano.width)), Image.LANCZOS)
    d = ImageDraw.Draw(rej)
    for i in range(1, 4):
        x = rej.width * i / 4
        y = rej.height * i / 4
        d.line([(x, 0), (x, rej.height)], fill=(255, 60, 60), width=2)
        d.line([(0, y), (rej.width, y)], fill=(60, 160, 255), width=2)
    rej.save(OUT / "_rejilla.png")
    print(" ", "_rejilla.png", rej.size)


if __name__ == "__main__":
    main()
