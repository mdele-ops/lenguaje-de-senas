"""Zoom 2 de la T: la esquina donde asoma el pulgar, con la lamina realzada.

La lamina del usuario trae la mano en 106x138 px y muy suave, asi que al
ampliarla se emborrona y no se distingue si el pulgar sale ENTRE el indice y el
medio o por fuera del indice. Aqui se sube primero la resolucion y despues se
realza el contorno (unsharp), que es lo que separa un dedo del de al lado.

Se sacan tambien tiras verticales de la lamina del proyecto (`referencia/T.png`)
para contar los dedos que asoman por arriba, que es la cuenta que decide la
pose: cuatro nudillos + una yema de pulgar entre el indice y el medio.
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / "tools" / "screenshots"
OUT = SHOTS / "zoom_t"
OUT.mkdir(parents=True, exist_ok=True)


def realza(im, lado):
    im = im.resize((lado, int(lado * im.height / im.width)), Image.LANCZOS)
    return im.filter(ImageFilter.UnsharpMask(radius=6, percent=180, threshold=2))


def guarda(im, nombre, lado):
    ruta = OUT / nombre
    realza(im, lado).save(ruta)
    print(" ", nombre, im.size, "->", lado)
    return ruta


def main():
    # --- lamina del usuario -------------------------------------------------
    lam = Image.open(SHOTS / "lamina_T.png").convert("RGB")
    mano = lam.crop((46, 30, 152, 168))
    guarda(mano, "n_mano_nitida.png", 900)
    # la esquina del pulgar: mitad derecha, tercio de arriba
    guarda(mano.crop((45, 0, 106, 60)), "n_pulgar.png", 900)
    # la fila de nudillos entera
    guarda(mano.crop((0, 5, 106, 55)), "n_nudillos.png", 1000)

    # --- lamina del proyecto ------------------------------------------------
    ref = Image.open(SHOTS / "referencia" / "T.png").convert("RGB")
    guarda(ref, "p_entera.png", 700)
    w, h = ref.size
    guarda(ref.crop((int(w * 0.25), int(h * 0.10), int(w * 0.80), int(h * 0.55))),
           "p_dedos.png", 900)

    # Tira horizontal a la altura de las puntas, con marcas cada 10 % para
    # poder contar cuantos dedos asoman y donde cae cada uno.
    tira = ref.crop((int(w * 0.25), int(h * 0.12), int(w * 0.80), int(h * 0.42)))
    tira = realza(tira, 900)
    d = ImageDraw.Draw(tira)
    for i in range(1, 10):
        x = tira.width * i / 10
        d.line([(x, 0), (x, tira.height)], fill=(255, 70, 70), width=1)
        d.text((x + 3, 4), str(i), fill=(255, 70, 70))
    tira.save(OUT / "p_tira.png")
    print("  p_tira.png", tira.size)
    print("Capturas en", OUT)


if __name__ == "__main__":
    main()
