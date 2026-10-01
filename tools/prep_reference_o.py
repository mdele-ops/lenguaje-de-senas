"""Recorta y amplia la referencia de la letra O que envio el usuario."""
from pathlib import Path

from PIL import Image

SRC = Path(
    r"C:\Users\KZTRDG\.cursor\projects\c-Users-KZTRDG-Documents-LENGUA-DE-SE-AS-PARTE-2"
    r"\assets\c__Users_KZTRDG_AppData_Roaming_Cursor_User_workspaceStorage"
    r"_918428176bcca0c3efb4b878bd61b4ca_images_image-b229e91b-3821-444a-9bdb-617c2668b782.png"
)
OUT = Path(__file__).resolve().parent / "screenshots" / "reference_o"
OUT.mkdir(parents=True, exist_ok=True)

im = Image.open(SRC).convert("RGB")
W, H = im.size
print("size", W, H)

im.resize((W * 4, H * 4), Image.LANCZOS).save(OUT / "ref_O_x4.png")

# Solo la zona de la mano (arriba del rotulo dorado)
hand = im.crop((0, 0, W, int(H * 0.78)))
hand.resize((hand.width * 5, hand.height * 5), Image.LANCZOS).save(
    OUT / "ref_O_mano_x5.png"
)
print("done ->", OUT)
