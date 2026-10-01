"""Cataloga la M con los tres dedos colgando y la muneca caida.

La version 1.3.25 los apretaba en puno. El usuario pidio que queden
"volando": indice/medio/anular casi extendidos, apuntando al piso. Eso
solo se lee si la muneca se inclina (~150 deg en X); si se deja en reposo
los dedos siguen mirando arriba.
"""
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from final_e15 import limpiar
from pose_lab_e import HAND_POS_JS, free_camera, set_cam
from pose_lab_m5 import hoja
from pose_lab_m8 import CASES, MEASURE_JS
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
CATALOGO = ROOT / "data" / "catalogo-lsm.json"
OUT = ROOT / "tools" / "screenshots" / "final_m8"
OUT.mkdir(parents=True, exist_ok=True)

DESCRIPCION = (
    "Índice, medio y anular cuelgan hacia abajo (como volando); la muñeca "
    "se inclina para que apunten al piso; el pulgar sujeta el meñique cerrado."
)


def main():
    cat = json.loads(CATALOGO.read_text("utf-8"))
    sena = next(x for x in cat["senas"] if x["letra"] == "M")
    anterior = json.loads(json.dumps(sena["pose"]))
    nueva = limpiar(CASES["D_x150_c12"])
    if "muneca" in nueva:
        nueva["muneca"] = {
            k: int(v) if float(v) == int(v) else v for k, v in nueva["muneca"].items()
        }

    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 900, "height": 950})
        time.sleep(0.3)
        viewer = page.query_selector("#viewer")
        free_camera(page)

        mano, prod = [], []
        for nombre, pz in (("1_ANTES", anterior), ("2_DESPUES", nueva)):
            page.evaluate(
                "(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pz
            )
            time.sleep(0.35)
            m = page.evaluate(MEASURE_JS)
            print(
                f"{nombre:12s} down={m['idxDown']:+.2f} hang={m['hang']:+.3f} "
                f"tog={m['togIM']:.3f}/{m['togMR']:.3f}"
            )
            hand = page.evaluate(HAND_POS_JS)
            set_cam(page, "mano", hand)
            p_m = OUT / f"{nombre}_mano.png"
            viewer.screenshot(path=str(p_m))
            mano.append((nombre, p_m))
            set_cam(page, "prod", hand)
            p_p = OUT / f"{nombre}_prod.png"
            viewer.screenshot(path=str(p_p))
            prod.append((nombre, p_p))
            set_cam(page, "lado", hand)
            viewer.screenshot(path=str(OUT / f"{nombre}_lado.png"))
        browser.close()

    hoja(mano, OUT / "_mano.png", cols=2, cell=320)
    hoja(prod, OUT / "_prod.png", cols=2, cell=320)

    sena["pose"] = nueva
    sena["descripcion"] = DESCRIPCION
    partes = cat["version"].split(".")
    partes[-1] = str(int(partes[-1]) + 1)
    cat["version"] = ".".join(partes)
    CATALOGO.write_text(
        json.dumps(cat, ensure_ascii=False, indent=2) + "\n", "utf-8"
    )
    print("catalogo version", cat["version"])
    (OUT / "_pose.json").write_text(
        json.dumps({"antes": anterior, "despues": nueva}, indent=2), "utf-8"
    )


if __name__ == "__main__":
    main()
