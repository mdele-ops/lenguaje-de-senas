"""T: la fila de nudillos de la pose, al lado de la de la lamina.

`revisa_t.py` saca la mano entera, y a ese tamano la yema del pulgar es un
bulto de treinta pixeles: no se puede decidir si se lee como pulgar o como un
quinto dedo. Aqui se recorta solo la franja donde estan las puntas —la mitad
de arriba— de la pose y de la lamina, y se ponen una encima de otra a la misma
anchura, que es la unica forma de comparar bultos.
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / "tools" / "screenshots"
OUT = SHOTS / "cerca_t"
OUT.mkdir(parents=True, exist_ok=True)

ANCHO = 920


def franja(im, alto=0.55):
    return im.crop((0, 0, im.width, int(im.height * alto)))


def escala(im, ancho=ANCHO):
    im = im.resize((ancho, int(ancho * im.height / im.width)), Image.LANCZOS)
    return im.filter(ImageFilter.UnsharpMask(radius=4, percent=140, threshold=2))


def main():
    piezas = []

    lam = Image.open(SHOTS / "lamina_T.png").convert("RGB").crop((46, 30, 152, 168))
    piezas.append(("lamina", escala(franja(lam))))

    for nombre in ("T_frente", "T_frente_esq", "T_tres_cuartos", "A_frente",
                   "S_frente"):
        ruta = SHOTS / "revisa_t" / f"{nombre}.png"
        if ruta.exists():
            piezas.append((nombre, escala(franja(Image.open(ruta).convert("RGB")))))

    alto = sum(p.height + 26 for _, p in piezas)
    hoja = Image.new("RGB", (ANCHO, alto), (14, 18, 30))
    d = ImageDraw.Draw(hoja)
    y = 0
    for nombre, p in piezas:
        hoja.paste(p, (0, y))
        y += p.height
        d.text((8, y + 7), nombre, fill=(235, 235, 235))
        y += 26
    hoja.save(OUT / "_franjas.png")
    print("Comparativa en", OUT / "_franjas.png")


if __name__ == "__main__":
    main()
