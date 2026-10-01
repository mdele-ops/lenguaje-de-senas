from PIL import Image
from pathlib import Path

SRC = Path(r"C:\Users\KZTRDG\.cursor\projects\c-Users-KZTRDG-Documents-LENGUA-DE-SE-AS-PARTE-2\assets\c__Users_KZTRDG_AppData_Roaming_Cursor_User_workspaceStorage_918428176bcca0c3efb4b878bd61b4ca_images_image-ee50c8ec-8000-4bbe-a40a-666897941759.png")
OUT = Path(__file__).resolve().parent / "screenshots" / "reference_crops"
OUT.mkdir(parents=True, exist_ok=True)

im = Image.open(SRC)
W, H = im.size
print("size", W, H)

# Approx grid: header ~0.205*H, footer ~0.135*H(from bottom), 3 rows of cards
header_h = int(H * 0.205)
footer_h = int(H * 0.135)
grid_top = header_h
grid_bottom = H - footer_h
row_h = (grid_bottom - grid_top) / 3

labels_row1 = ["A","B","C","D","E","F","G","H","I","J"]
labels_row2 = ["K","L","LL","M","N","N~","O","P","Q","R"]
labels_row3 = ["RR","S","T","U","V","W","X","Y","Z"]

def crop_row(labels, row_idx):
    n = len(labels)
    col_w = W / 10.0  # always divide by 10 since card width is consistent across rows
    top = int(grid_top + row_idx*row_h)
    bottom = int(grid_top + (row_idx+1)*row_h)
    for i, lab in enumerate(labels):
        left = int(i*col_w)
        right = int((i+1)*col_w)
        crop = im.crop((left, top, right, bottom))
        crop = crop.resize((crop.width*2, crop.height*2))
        safe = lab.replace("~","tilde")
        crop.save(OUT / f"row{row_idx}_{i:02d}_{safe}.png")

crop_row(labels_row1, 0)
crop_row(labels_row2, 1)
crop_row(labels_row3, 2)
print("done")
