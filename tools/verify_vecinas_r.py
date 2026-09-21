"""Regresion alrededor de la R: que no se confunda con sus vecinas de forma.

La R comparte esqueleto con la U (indice y medio juntos), la V (separados) y la
W (tres dedos): las cuatro sacan los mismos dedos y solo cambian de reparto. Se
aplican desde el catalogo real y se comprueba que solo la R sale cruzada, para
que arreglar la R no haya estropeado a las vecinas.
"""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from enfoque_r import MANO, captura, hoja
from eje_r import CAM_FOV, CAM_ORBIT, CAM_TARGET, cam
from pose_lab_e import free_camera
from pose_lab_r import MEASURE_JS
import search_e9 as se9
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "verify_vecinas_r"
OUT.mkdir(parents=True, exist_ok=True)

se9.URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=vecr"

LETRAS = ["D", "U", "V", "W", "R"]


def main():
    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 1000, "height": 1000})
        time.sleep(0.3)
        free_camera(page)

        total = page.evaluate(
            "() => window.__LSM_CONTROLLER__.getCatalog().senas.length"
        )
        print("senas en el catalogo:", total)

        items, fallos = [], []
        for letra in LETRAS:
            r = page.evaluate("(l) => window.__LSM_CONTROLLER__.mostrarSena(l)", letra)
            time.sleep(2.5)
            m = page.evaluate(MEASURE_JS)
            cruzada = m["cruce"] > 0.5
            print(
                f"{letra:2s} modo={r['modo']:8s} cruce={m['cruce']:+6.2f} "
                f"gap={m['gap']:.3f} frente={m['frenteMed']:+5.2f} "
                f"yemas={m['sepYemas']:.2f}  {'CRUZADA' if cruzada else '-'}"
            )
            # solo la R va cruzada, y ninguna puede tener los dedos metidos
            # uno dentro del otro
            if cruzada != (letra == "R"):
                fallos.append(f"{letra}: cruce {m['cruce']:+.2f}")
            if m["gap"] < 0.10:
                fallos.append(f"{letra}: dedos superpuestos (gap {m['gap']:.3f})")

            cam(page, CAM_TARGET, CAM_ORBIT, CAM_FOV)
            ruta = OUT / f"{letra}.png"
            captura(page, ruta, MANO, margen=0.28)
            items.append((letra, ruta))

        browser.close()

    hoja(items, OUT / "_vecinas.png", cols=5, cell=320, titulo="R y sus vecinas")
    print("\n  " + ("TODO OK" if not fallos else "REVISAR: " + "; ".join(fallos)))


if __name__ == "__main__":
    main()
