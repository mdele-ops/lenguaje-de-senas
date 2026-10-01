"""Hoja de comparacion de la S: lamina, version anterior y version nueva.

Arriba, de frente, que es como la ve el usuario: la S anterior no cruzaba nada
(el pulgar se descolgaba por la palma, medio palmo por debajo de los dedos, asi
que se leia como una A mal cerrada) y la nueva lo tumba por delante del puno.

Abajo, de perfil, que es donde se ve el fallo que de frente no se nota: antes
el pulgar salia disparado hacia fuera del puno en vez de apoyarse en los dedos.
"""
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / "tools" / "screenshots"

FRENTE = [
    ("Lamina oficial (LSM)", SHOTS / "final_s" / "_ref.png"),
    ("Antes: pulgar caido por la palma", SHOTS / "ver_s" / "S_actual_frente.png"),
    ("Ahora: pulgar cruzado delante", SHOTS / "verify_s" / "S_frente.png"),
]
LADO = [
    ("Antes: pulgar fuera del puno", SHOTS / "ver_s" / "S_actual_perfil.png"),
    ("Ahora: pulgar apoyado", SHOTS / "verify_s" / "S_perfil.png"),
    ("Ahora: tres cuartos", SHOTS / "verify_s" / "S_tres_cuartos.png"),
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
    salida = SHOTS / "S_antes_despues.png"
    hoja.save(salida)
    print("Hoja:", salida)


if __name__ == "__main__":
    main()
