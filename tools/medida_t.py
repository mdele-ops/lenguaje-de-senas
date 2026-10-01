"""Que numeros da la lamina de la T, medidos sobre la propia lamina.

Hasta aqui los rangos de `search_t.py` eran a ojo ("que asome un poco"). Se
pueden sacar de la foto: las dos medidas que definen la letra son adimensionales
(se dividen por el ancho del puno), asi que valen igual en la lamina que en el
modelo y se pueden comparar directamente.

Los puntos se marcan a mano sobre `zoom_t/n_mano_nitida.png` (900 px de ancho,
recorte (46,30)-(152,168) de la lamina). Se dibuja encima para poder comprobar
que estan donde se dice.
"""
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "zoom_t"
FUENTE = OUT / "n_mano_nitida.png"

# Puntos leidos sobre n_mano_nitida.png (900 px de ancho).
#   nudillo = lo alto del bulto de cada dedo doblado
#   cima    = el pixel mas alto de ese bulto
PUNTOS = {
    "yema_pulgar": (530, 75),     # la punta rosa que asoma
    "nudillo_indice": (640, 200),
    "cima_indice": (640, 130),
    "nudillo_medio": (430, 215),
    "cima_medio": (430, 145),
    "nudillo_menique": (150, 330),
}


def main():
    p = PUNTOS
    # ancho del puno: del nudillo del indice al del menique, que es la unidad
    # en la que van todas las medidas del modelo
    ancho = (
        (p["nudillo_indice"][0] - p["nudillo_menique"][0]) ** 2
        + (p["nudillo_indice"][1] - p["nudillo_menique"][1]) ** 2
    ) ** 0.5

    # lo mas alto del puno (y crece hacia abajo, asi que es el minimo)
    cima = min(p["cima_indice"][1], p["cima_medio"][1])
    camCima = (cima - p["yema_pulgar"][1]) / ancho

    # la muesca entre indice y medio, y donde cae la yema respecto a ella
    muesca_x = (p["nudillo_indice"][0] + p["nudillo_medio"][0]) / 2
    camDesvio = (p["yema_pulgar"][0] - muesca_x) / ancho
    # y en las mismas unidades que camU: 0 = nudillo indice, 1 = menique
    camU = (p["yema_pulgar"][0] - p["nudillo_indice"][0]) / (
        p["nudillo_menique"][0] - p["nudillo_indice"][0]
    )

    print(f"  ancho del puno   {ancho:7.1f} px")
    print(f"  camCima          {camCima:+7.3f}   (la yema asoma por encima)")
    print(f"  camDesvio        {camDesvio:+7.3f}   (0 = justo en la muesca)")
    print(f"  camU             {camU:+7.3f}   (0 = indice, 1 = menique)")

    im = Image.open(FUENTE).convert("RGB")
    d = ImageDraw.Draw(im)
    for nombre, (x, y) in p.items():
        col = (235, 30, 30) if "pulgar" in nombre else (40, 130, 245)
        d.ellipse([x - 7, y - 7, x + 7, y + 7], fill=col)
        d.text((x + 10, y - 6), nombre, fill=col)
    d.line([p["nudillo_indice"], p["nudillo_menique"]], fill=(40, 200, 80), width=3)
    d.line([(muesca_x, 0), (muesca_x, im.height)], fill=(255, 150, 20), width=2)
    d.line([(0, cima), (im.width, cima)], fill=(255, 150, 20), width=2)
    ruta = OUT / "_medida.png"
    im.save(ruta)
    print("  comprobacion en", ruta.name)


if __name__ == "__main__":
    main()
