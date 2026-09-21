"""W lab 2: que eje abre el anular a izquierda-derecha en pantalla.

El lab 1 dejo claro que spread +z en el anular sube el angulo 3D (MR 13->40)
pero el angulo de pantalla se queda en 10-18 deg: el anular se abre en
profundidad, no en el plano de la foto. La lamina pide tres palitos de la W
separados de lado. Este lab parte de indice abierto (spread -14) + pulgar de
la U/V y barre x/y/z del nudillo del anular, con encuadre cercano.
"""
import shutil
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from eje_r import encuadrar
from enfoque_r import MANO, captura, hoja
from pose_lab_e import BONES, T1, T2, free_camera
from pose_lab_r import MEASURE_JS
from pose_lab_w import ANGLE_JS, PULGAR_UV, linea, pose_w
import search_e9 as se9
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "lab_w2"
OUT.mkdir(parents=True, exist_ok=True)
REF_SRC = Path(
    r"C:\Users\KZTRDG\.cursor\projects"
    r"\c-Users-KZTRDG-General-Motors-Christian-Osvaldo-Partida-Cadena-Becarios-Manu-Lenguaje-de-se-as"
    r"\assets"
    r"\c__Users_KZTRDG_AppData_Roaming_Cursor_User_workspaceStorage"
    r"_e58e5485bac69e9b6ccd69cb178bd5da_images"
    r"_image-62298505-9f0f-4b8d-bc0a-ba50cb2c2c18.png"
)
REF = ROOT / "tools" / "screenshots" / "referencia" / "W_usuario.png"

se9.URL = "http://127.0.0.1:8006/practica.html?letra=%E2%97%8B&v=w2"

RING1 = BONES["ring"][0]


def pose_ex(iz=-14, mz=0, rz=0, ring=None, thumb=None, tcurl=0.35):
    p = pose_w(iz=iz, mz=mz, rz=rz, tcurl=tcurl, thumb=thumb)
    if ring:
        p["extra"][RING1] = dict(ring)
    return p


def asegurar_ref():
    REF.parent.mkdir(parents=True, exist_ok=True)
    src = REF_SRC
    # el archivo vive plano en assets/, no en subcarpetas
    plano = Path(
        r"C:\Users\KZTRDG\.cursor\projects"
        r"\c-Users-KZTRDG-General-Motors-Christian-Osvaldo-Partida-Cadena-Becarios-Manu-Lenguaje-de-se-as"
        r"\assets"
        r"\c__Users_KZTRDG_AppData_Roaming_Cursor_User_workspaceStorage"
        r"_e58e5485bac69e9b6ccd69cb178bd5da_images_image-62298505-9f0f-4b8d-bc0a-ba50cb2c2c18.png"
    )
    if plano.exists():
        shutil.copy2(plano, REF)
    elif src.exists():
        shutil.copy2(src, REF)
    return REF if REF.exists() else None


def main():
    casos = {
        "00_base_i-14": pose_ex(),
        "01_r_x-20": pose_ex(ring={"x": -20}),
        "02_r_x20": pose_ex(ring={"x": 20}),
        "03_r_y-20": pose_ex(ring={"y": -20}),
        "04_r_y20": pose_ex(ring={"y": 20}),
        "05_r_z-20": pose_ex(ring={"z": -20}),
        "06_r_z20": pose_ex(ring={"z": 20}),
        "07_r_y-35": pose_ex(ring={"y": -35}),
        "08_r_y35": pose_ex(ring={"y": 35}),
        "09_m10_r_y20": pose_ex(mz=10, ring={"y": 20}),
        "10_m10_r_z20": pose_ex(mz=10, ring={"z": 20}),
        "11_i-18_r_y25": pose_ex(iz=-18, ring={"y": 25}),
    }

    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 900, "height": 900})
        time.sleep(0.4)
        free_camera(page)

        ref = asegurar_ref()
        items = [("REF foto", ref)] if ref else []
        medidas = {}
        for nombre, pose in casos.items():
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
            time.sleep(0.35)
            m = page.evaluate(MEASURE_JS)
            a = page.evaluate(ANGLE_JS)
            medidas[nombre] = {**m, **a}
            if m.get("error") or a.get("error"):
                print(" ", nombre, m, a)
                continue
            print(" ", linea(nombre, m, a))
            encuadrar(page, 0)
            ruta = OUT / f"{nombre}.png"
            captura(page, ruta, MANO, margen=0.22, lado=560)
            items.append((nombre, ruta))

        browser.close()

    hoja(items, OUT / "_hoja.png", cols=4, cell=340, titulo="W · lab 2 · eje anular")
    (OUT / "_medidas.json").write_text(
        __import__("json").dumps(medidas, indent=2), encoding="utf-8"
    )
    print("Capturas en", OUT)
    print("REF:", REF if REF.exists() else "NO")


if __name__ == "__main__":
    main()
