"""Q lab 3: abrir el pico indice-pulgar.

La familia A del lab 2 ya deja la mano colgando con el indice apuntando al
suelo, pero el pulgar se queda recogido y en pantalla la letra se lee como una
G/D hacia abajo, sin el hueco que hace la Q. En la lamina el pulgar cuelga
estirado por dentro del indice y su yema queda MAS BAJA que la del indice.

Objetivos leidos en la rejilla de la lamina:
    pulgar en pantalla     ~ -105 grados
    apertura del pico      ~   35 grados
    separacion de yemas    ~  1.19 largos de palma
    yema del pulgar        ~  0.80 palmas por debajo de la del indice
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
OUT = ROOT / "tools" / "screenshots" / "lab_q3"
OUT.mkdir(parents=True, exist_ok=True)

se9.URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=q3"

OBJ = {"th": -105.0, "pico": 35.0, "sep": 1.19, "bajo": 0.80}


def banda(v, lo, hi):
    if v < lo:
        return lo - v
    if v > hi:
        return v - hi
    return 0.0


def puntuar(m):
    p = 0.30 * abs(m["thAng"] - OBJ["th"])
    p += 0.30 * abs(apertura(m) - OBJ["pico"])
    p += 12.0 * abs(m["pico"] - OBJ["sep"])
    p += 8.0 * abs(m["thBajoIdx"] - OBJ["bajo"])
    # el indice tiene que seguir bajando y la mano de tres cuartos, no de frente
    p += 20.0 * banda(m["idxAng"], -150.0, -125.0)
    p += 15.0 * banda(abs(m["palmNz"]), 0.0, 0.55)
    return p


def main():
    rejilla = list(
        itertools.product(
            (0.0, 0.15, 0.3),        # tcurl: cuanto se recoge el pulgar
            (0.0, 0.3, 0.6),         # taside: cuanto se abre del indice
            (-40, -20, 0, 20),       # t1 y
            (-20, 0, 20),            # t1 z
            (0, 20),                 # t2 x
        )
    )

    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 1100, "height": 900})
        time.sleep(0.4)
        viewer = page.query_selector("#viewer")
        free_camera(page)

        res = []
        for tcurl, taside, t1y, t1z, t2x in rejilla:
            pose = pose_q(
                wx=135, wz=45, idx_dip=35,
                tcurl=tcurl, taside=taside, t1y=t1y, t1z=t1z, t2x=t2x,
            )
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
            m = page.evaluate(MEASURE_JS)
            res.append((puntuar(m), (tcurl, taside, t1y, t1z, t2x), m))
        res.sort(key=lambda t: t[0])

        print(f"{len(rejilla)} combinaciones de pulgar. Objetivo {OBJ}")
        for s, k, m in res[:12]:
            print(
                f"  tc{k[0]:<5} as{k[1]:<4} y{k[2]:<4} z{k[3]:<4} t2{k[4]:<3} "
                f"score={s:6.2f} th={m['thAng']:+7.1f} pico={apertura(m):5.1f} "
                f"sep={m['pico']:.2f} bajo={m['thBajoIdx']:+.2f} "
                f"idx={m['idxAng']:+7.1f} palmNz={m['palmNz']:+.2f}"
            )

        prod = [("REF lamina", REF)] if REF.exists() else []
        cerca = list(prod)
        elegidos = {}
        for s, k, m in res[:8]:
            elegidos[f"tc{k[0]}_as{k[1]}_y{k[2]}_z{k[3]}_t2{k[4]}"] = pose_q(
                wx=135, wz=45, idx_dip=35,
                tcurl=k[0], taside=k[1], t1y=k[2], t1z=k[3], t2x=k[4],
            )
        for nombre, pose in elegidos.items():
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
            time.sleep(0.3)
            cam(page, CAM_TARGET, CAM_ORBIT, CAM_FOV)
            path = OUT / f"{nombre}.png"
            viewer.screenshot(path=str(path))
            prod.append((nombre, path))

            mano = page.evaluate(HAND_POS_JS)
            cam(
                page,
                "%.3fm %.3fm %.3fm" % (mano["x"], mano["y"] - 0.04, mano["z"]),
                "0deg 84deg 1.00m",
                "21deg",
            )
            zoom = OUT / f"{nombre}_zoom.png"
            viewer.screenshot(path=str(zoom))
            cerca.append((nombre, zoom))

        browser.close()

    hoja(prod, OUT / "_produccion.png", cols=3, cell=340, caja=(150, 120, 480, 450))
    hoja(cerca, OUT / "_cerca.png", cols=3, cell=340)
    (OUT / "_casos.json").write_text(json.dumps(elegidos, indent=2), "utf-8")


if __name__ == "__main__":
    main()
