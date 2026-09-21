"""Copia y amplia la imagen de referencia de la letra C para inspeccion."""
import shutil
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC = Path(
    r"C:\Users\KZTRDG\.cursor\projects\c-Users-KZTRDG-Documents-LENGUA-DE-SE-AS-PARTE-2"
    r"\assets\c__Users_KZTRDG_AppData_Roaming_Cursor_User_workspaceStorage"
    r"_918428176bcca0c3efb4b878bd61b4ca_images_image-faf3fcbe-0d4a-4217-bc0f-5b68c1095bfe.png"
)
OUT = ROOT / "tools" / "screenshots" / "ref_c"
OUT.mkdir(parents=True, exist_ok=True)


def main():
    shutil.copyfile(SRC, OUT / "ref_c_original.png")
    img = Image.open(SRC).convert("RGB")
    print("tamano original:", img.size)
    scale = max(1, 700 // max(img.size))
    big = img.resize((img.width * scale, img.height * scale), Image.LANCZOS)
    big.save(OUT / "ref_c_grande.png")
    print("ampliada:", big.size, "x", scale)


if __name__ == "__main__":
    main()
