"""Hoja de comparacion de la R: lamina, version anterior y version nueva.

Arriba, de frente, que es como la ve el usuario: la R anterior abria los dedos
en V (era una V con los dedos metidos uno en otro) y la nueva los cruza.
Abajo, de perfil y de tres cuartos, que es donde se ven los dos fallos que no
se notaban de frente: los dedos ocupando el mismo sitio y el pulgar en
escuadra.
"""
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / "tools" / "screenshots"

FRENTE = [
    ("Lamina oficial (LSM)", SHOTS / "lamina_R.png"),
    ("Antes: V con los dedos metidos", SHOTS / "final_r" / "00_R_vieja_frente.png"),
    ("Ahora: indice cruzado delante", SHOTS / "verify_r" / "R_frente.png"),
]
LADO = [
    ("Antes: pulgar en escuadra", SHOTS / "final_r" / "00_R_vieja_perfil.png"),
    ("Ahora: pulgar tumbado", SHOTS / "verify_r" / "R_perfil.png"),
    ("Ahora: tres cuartos", SHOTS / "verify_r" / "R_tres_cuartos.png"),
]

CELL = 340
LH = 28


def recuadro(path):
    im = Image.open(path).convert("RGB")
    lado = min(im.size)
    return im.crop(
        (
            (im.width - lado) // 2,
            (im.height - lado) // 2,
            (im.width + lado) // 2,
            (im.height + lado) // 2,
        )
    ).resize((CELL, CELL), Image.LANCZOS)


def main():
    cols = max(len(FRENTE), len(LADO))
    hoja = Image.new("RGB", (CELL * cols, 2 * (CELL + LH)), (245, 245, 248))
    draw = ImageDraw.Draw(hoja)
    for fila, paneles in enumerate((FRENTE, LADO)):
        for i, (titulo, path) in enumerate(paneles):
            if not path.exists():
                print("falta:", path)
                continue
            x, y = i * CELL, fila * (CELL + LH)
            hoja.paste(recuadro(path), (x, y))
            draw.rectangle([x, y + CELL, x + CELL, y + CELL + LH], fill=(20, 30, 50))
            draw.text((x + 8, y + CELL + 9), titulo, fill=(255, 255, 255))
    salida = SHOTS / "R_antes_despues.png"
    hoja.save(salida)
    print("Hoja:", salida)


if __name__ == "__main__":
    main()
