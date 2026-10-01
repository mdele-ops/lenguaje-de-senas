"""Q lab 4: el gancho de la yema del indice y el ajuste final de la muneca.

Con el pulgar del lab 3 el pico ya se lee. Falta lo que en la lamina distingue
la Q de un simple dedo que apunta al suelo: la yema del indice va CURVADA
hacia el pulgar, como un garfio, y el hueco entre las dos yemas queda ovalado.

Se barren los grados de la falange media (pip) y de la yema (dip) del indice
junto con el giro de la muneca, porque al curvar el dedo el angulo del indice
en pantalla se cierra y hay que devolverlo a ~-135.
"""
import itertools
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from pose_lab_e import HAND_POS_JS, free_camera
from pose_lab_p7 import CAM_FOV, CAM_ORBIT, CAM_TARGET, hoja
from pose_lab_q import MEASURE_JS, REF, pose_q
from pose_lab_q2 import apertura, cam
import search_e9 as se9
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "lab_q4"
OUT.mkdir(parents=True, exist_ok=True)

se9.URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=q4"

PULGAR = dict(tcurl=0.3, taside=0.3, t1y=-40, t1z=-20, t2x=0)


def casos():
    c = {}
    for pip, dip in itertools.product((0, 15, 30), (30, 45, 60)):
        c[f"h_pip{pip}_dip{dip}"] = pose_q(
            wx=135, wz=45, idx_pip=pip, idx_dip=dip, **PULGAR
        )
    for wx, wz in itertools.product((128, 135, 142), (40, 50)):
        c[f"w_x{wx}_z{wz}"] = pose_q(
            wx=wx, wz=wz, idx_pip=15, idx_dip=45, **PULGAR
        )
    return c


def main():
    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 1100, "height": 900})
        time.sleep(0.4)
        viewer = page.query_selector("#viewer")
        free_camera(page)

        prod = [("REF lamina", REF)] if REF.exists() else []
        cerca = list(prod)
        elegidos = casos()

        for nombre, pose in elegidos.items():
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
            time.sleep(0.3)
            m = page.evaluate(MEASURE_JS)
            print(
                f"  {nombre:18s} idx={m['idxAng']:+7.1f} th={m['thAng']:+7.1f} "
                f"pico={apertura(m):5.1f} sep={m['pico']:.2f} "
                f"hook={m['idxHook']:.2f} largoIdx={m['idxScr']:.2f} "
                f"palmNz={m['palmNz']:+.2f}"
            )

            cam(page, CAM_TARGET, CAM_ORBIT, CAM_FOV)
            path = OUT / f"{nombre}.png"
            viewer.screenshot(path=str(path))
            prod.append((nombre, path))

            mano = page.evaluate(HAND_POS_JS)
            cam(
                page,
                "%.3fm %.3fm %.3fm" % (mano["x"], mano["y"] - 0.04, mano["z"]),
                "0deg 84deg 0.95m",
                "21deg",
            )
            zoom = OUT / f"{nombre}_zoom.png"
            viewer.screenshot(path=str(zoom))
            cerca.append((nombre, zoom))

        browser.close()

    hoja(prod, OUT / "_produccion.png", cols=4, cell=330, caja=(150, 120, 480, 450))
    hoja(cerca, OUT / "_cerca.png", cols=4, cell=330)
    (OUT / "_casos.json").write_text(json.dumps(elegidos, indent=2), "utf-8")


if __name__ == "__main__":
    main()
