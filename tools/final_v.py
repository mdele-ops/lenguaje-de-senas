"""V final: V estrecha (~32 deg) con el pulgar de la U.

La V del catalogo usa spread +-42 (84 deg 3D, 145 deg en pantalla) y el pulgar
se queda de pie al costado. La foto pide 30-35 deg y el pulgar tumbado sobre
anular y menique. Este script compara las tres aberturas que cayeron en ese
rango, encuadradas de cerca.
"""
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from eje_r import CAM_FOV, CAM_ORBIT, CAM_TARGET, cam, encuadrar
from enfoque_r import MANO, captura, hoja
from pose_lab_e import T1, T2, free_camera
from pose_lab_u import pose_u
from pose_lab_v import ANGLE_JS, linea
from pose_lab_r import MEASURE_JS
from search_e9 import abrir
import search_e9 as se9

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "final_v"
OUT.mkdir(parents=True, exist_ok=True)
REF = ROOT / "tools" / "screenshots" / "referencia" / "V_usuario.png"
CATALOGO = ROOT / "data" / "catalogo-lsm.json"

se9.URL = "http://127.0.0.1:8006/practica.html?letra=%E2%97%8B&v=vfin"


def pose_guardar(iz, mz):
    """Pose lista para el catalogo: spread semantico + pulgar de la U, sin brazo."""
    return {
        "thumb": {"curl": 0.35, "aside": -0.6},
        "index": {"curl": 0.0, "spread": iz},
        "middle": {"curl": 0.0, "spread": mz},
        "ring": {"curl": 0.95},
        "pinky": {"curl": 0.95},
        "extra": {
            T1: {"y": -30, "z": 40},
            T2: {"x": 60},
        },
    }


FINALISTAS = {
    "A_z-10": pose_guardar(-10, 10),
    "B_z-11": pose_guardar(-11, 11),
    "C_z-12": pose_guardar(-12, 12),
}

DESCRIPCION = (
    "Índice y medio estirados hacia arriba y separados en una V estrecha "
    "(unos 30-35 grados, no el signo de victoria abierto). Anular y meñique "
    "se recogen en el puño con el pulgar tumbado encima, apoyado sobre las "
    "falanges de esos dos, sin montar en los dedos largos."
)


def guardar(pose):
    datos = json.loads(CATALOGO.read_text(encoding="utf-8"))
    sena = next(s for s in datos["senas"] if s["letra"] == "V")
    sena["pose"] = pose
    sena["descripcion"] = DESCRIPCION
    partes = datos["version"].split(".")
    partes[-1] = str(int(partes[-1]) + 1)
    datos["version"] = ".".join(partes)
    CATALOGO.write_text(
        json.dumps(datos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Catalogo actualizado (version {datos['version']})")


def main():
    catalogo = json.loads(CATALOGO.read_text(encoding="utf-8"))
    vieja = next(s for s in catalogo["senas"] if s["letra"] == "V")["pose"]
    casos = {"00_catalogo": vieja, **FINALISTAS}

    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 900, "height": 900})
        time.sleep(2.2)
        free_camera(page)
        viewer = page.query_selector("#viewer")

        items = [("REF foto", REF)] if REF.exists() else []
        medidas = {}
        for nombre, pose in casos.items():
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
            time.sleep(0.45)
            m = page.evaluate(MEASURE_JS)
            a = page.evaluate(ANGLE_JS)
            medidas[nombre] = {**m, **a}
            print(" ", linea(nombre, m, a) if not m.get("error") else (nombre, m))

            cam(page, CAM_TARGET, CAM_ORBIT, CAM_FOV)
            visor = OUT / f"{nombre}_prod.png"
            viewer.screenshot(path=str(visor))
            items.append((nombre + " prod", visor))

            encuadrar(page, 0)
            mano = OUT / f"{nombre}_mano.png"
            captura(page, mano, MANO, margen=0.22, lado=560)
            items.append((nombre + " mano", mano))

        browser.close()

    hoja(items, OUT / "_hoja.png", cols=3, cell=380, titulo="V · finalistas")
    (OUT / "_poses.json").write_text(
        json.dumps(FINALISTAS, indent=2), encoding="utf-8"
    )
    (OUT / "_medidas.json").write_text(
        json.dumps(medidas, indent=2), encoding="utf-8"
    )
    print("Capturas en", OUT)


if __name__ == "__main__":
    import sys

    main()
    if "--guardar" in sys.argv:
        cual = "A_z-10"
        if len(sys.argv) > sys.argv.index("--guardar") + 1:
            cual = sys.argv[sys.argv.index("--guardar") + 1]
        guardar(FINALISTAS[cual])
