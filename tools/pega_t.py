"""T: la lamina y la pose, recortadas al puno y puestas al mismo ancho.

Con la camara pegada (`lupa_t.py`) las capturas ya tienen pixeles de verdad,
pero siguen sin poder compararse con la lamina: cada una trae el puno a un
tamano. Aqui se recorta el puno en las dos y se llevan al mismo ancho, que es
la unica manera de responder a la pregunta que queda: cuanto pulgar se ve.

En la lamina el pulgar asoma un pellizco (la yema y poco mas, porque el indice
tapa el resto). Si en la pose se ve el pulgar entero de arriba abajo, la mano
dice otra cosa aunque la yema caiga donde toca.
"""
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / "tools" / "screenshots"
OUT = SHOTS / "pega_t"
OUT.mkdir(parents=True, exist_ok=True)

ANCHO = 760

# Recortes del puno: (x0, y0, x1, y1) en cada fuente.
PUNO = {
    "lamina": (SHOTS / "zoom_t" / "n_mano_nitida.png", (40, 40, 720, 640)),
    "T": (SHOTS / "lupa_t" / "T_frente.png", (230, 200, 680, 500)),
    "A": (SHOTS / "lupa_t" / "A_frente.png", (230, 200, 700, 500)),
    "S": (SHOTS / "lupa_t" / "S_frente.png", (230, 200, 700, 500)),
}

# Y la muesca sola: los dos dedos de al lado y lo que asoma entre ellos, que es
# donde esta toda la letra. La caja de la lamina es la misma que usa
# `zoom_t2.py` para `n_pulgar.png`.
MUESCA = {
    "lamina": (SHOTS / "zoom_t" / "n_pulgar.png", None),
    "T": (SHOTS / "lupa_t" / "T_frente.png", (420, 190, 700, 480)),
}


def tira(recortes, destino):
    piezas = []
    for nombre, (ruta, caja) in recortes.items():
        if not ruta.exists():
            continue
        im = Image.open(ruta).convert("RGB")
        if caja:
            im = im.crop(caja)
        im = im.resize((ANCHO, int(ANCHO * im.height / im.width)), Image.LANCZOS)
        piezas.append((nombre, im))

    alto = sum(p.height + 24 for _, p in piezas)
    hoja = Image.new("RGB", (ANCHO, alto), (14, 18, 30))
    d = ImageDraw.Draw(hoja)
    y = 0
    for nombre, p in piezas:
        hoja.paste(p, (0, y))
        y += p.height
        d.text((8, y + 6), nombre, fill=(240, 240, 240))
        y += 24
    hoja.save(destino)
    print("Comparativa en", destino)


def main():
    tira(PUNO, OUT / "_puno.png")
    tira(MUESCA, OUT / "_muesca.png")


if __name__ == "__main__":
    main()
