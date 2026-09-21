"""Pone la lamina de la T al lado de sus vecinas de puno (A, E, S, M, N).

Las seis son el mismo puno y solo cambia el pulgar, asi que la unica forma de
leer la T sin equivocarse es verlas juntas y a buen tamano: en la A el pulgar
sube por el costado, en la S cruza por delante y en la T se mete ENTRE dos
dedos. Tambien se amplia la lamina propia del proyecto
(`referencia/T.png`), que esta dibujada de frente y sin sombras.
"""
from pathlib import Path

from PIL import Image

from enfoque_r import hoja

ROOT = Path(__file__).resolve().parents[1]
REFS = ROOT / "tools" / "screenshots" / "referencia"
USUARIO = ROOT / "tools" / "screenshots" / "lamina_T.png"
OUT = ROOT / "tools" / "screenshots" / "ref_t"
OUT.mkdir(parents=True, exist_ok=True)

VECINAS = ("A", "E", "S", "T", "M", "N")


def grande(src, dst, lado=520):
    im = Image.open(src).convert("RGB")
    im.resize((lado, int(lado * im.height / im.width)), Image.LANCZOS).save(dst)
    return dst


def main():
    items = []
    for letra in VECINAS:
        src = REFS / f"{letra}.png"
        if src.exists():
            items.append((f"ref {letra}", grande(src, OUT / f"ref_{letra}.png")))
    items.append(("lamina usuario T", grande(USUARIO, OUT / "usuario_T.png")))

    hoja(items, OUT / "_hoja.png", cols=4, cell=380, titulo="T y sus vecinas de puno")

    # Y la lamina del proyecto sola, lo mas grande posible.
    grande(REFS / "T.png", OUT / "_T_big.png", 900)
    print("Capturas en", OUT)


if __name__ == "__main__":
    main()
