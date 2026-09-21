"""Q lab 2: las dos maneras de dejar el pico apuntando al suelo.

Leyendo la lamina sobre la rejilla (ref_Q_rejilla.png) salen estos angulos en
pantalla (0 = a la derecha, 90 = hacia arriba):

    eje de la mano (muneca -> nudillo del medio)   ~ +150
    indice (nudillo -> yema)                       ~ -140
    pulgar (base -> yema)                          ~ -105
    apertura del pico indice-pulgar                ~   35

O sea: el dorso queda casi horizontal y son los DEDOS los que bajan, doblados
unos 70 grados en el nudillo. Hay dos formas de llegar ahi y no dan lo mismo
en pantalla:

  A  doblar la muneca (como en la N/Ñ, wx ~150): la mano entera cuelga y el
     indice sale recto, en linea con el dorso.
  B  doblar el nudillo del indice sobre una mano casi horizontal: es lo que
     hace la lamina, pero con el brazo del avatar pegado al cuerpo la palma
     puede acabar mirando a la camara.

Se comparan ambas contra la lamina, midiendo la apertura del pico (que es lo
que hace legible la letra) y que el pico caiga hacia abajo.
"""
import itertools
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from pose_lab_e import HAND_POS_JS, free_camera
from pose_lab_p7 import CAM_FOV, CAM_ORBIT, CAM_TARGET, hoja
from pose_lab_q import MEASURE_JS, REF, pose_q
import search_e9 as se9
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "lab_q2"
OUT.mkdir(parents=True, exist_ok=True)

se9.URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=q2"

OBJ_PICO = 35.0      # apertura indice-pulgar en pantalla
OBJ_IDX = -140.0     # el indice cae hacia abajo y algo hacia la izquierda
OBJ_TH = -105.0


def apertura(m):
    """Angulo en pantalla entre indice y pulgar (siempre positivo)."""
    d = abs(m["idxAng"] - m["thAng"]) % 360
    return min(d, 360 - d)


def linea(nombre, m):
    return (
        f"{nombre:26s} idx={m['idxAng']:+7.1f} th={m['thAng']:+7.1f} "
        f"pico={apertura(m):5.1f} sep={m['pico']:.2f} mano={m['manoAng']:+7.1f} "
        f"palmN=({m['palmNx']:+.2f},{m['palmNz']:+.2f}) hook={m['idxHook']:.2f}"
    )


def cam(page, target, orbit, fov):
    page.evaluate(
        """(a) => {
            const mv = document.getElementById('handViewer');
            mv.cameraTarget = a.t;
            mv.cameraOrbit = a.orbit;
            mv.fieldOfView = a.fov;
            mv.jumpCameraToGoal();
        }""",
        {"t": target, "orbit": orbit, "fov": fov},
    )
    time.sleep(0.25)


def casos():
    c = {}
    # Familia A: la muneca dobla y el indice sale recto con la yema enganchada.
    for wx, wz in itertools.product((135, 150, 165), (20, 35, 50)):
        c[f"A_x{wx}_z{wz}"] = pose_q(wx=wx, wz=wz, idx_dip=35, t1y=-20)
    # Familia B: mano casi horizontal y el nudillo del indice baja el dedo.
    for wx, mcp in itertools.product((60, 90), (55, 70, 85)):
        c[f"B_x{wx}_mcp{mcp}"] = pose_q(wx=wx, idx_mcp=mcp, idx_dip=35, t1y=-20)
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

        print(f"objetivo: pico={OBJ_PICO} idx={OBJ_IDX} th={OBJ_TH}")
        for nombre, pose in elegidos.items():
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
            time.sleep(0.3)
            print(" ", linea(nombre, page.evaluate(MEASURE_JS)))

            cam(page, CAM_TARGET, CAM_ORBIT, CAM_FOV)
            path = OUT / f"{nombre}.png"
            viewer.screenshot(path=str(path))
            prod.append((nombre, path))

            mano = page.evaluate(HAND_POS_JS)
            cam(
                page,
                "%.3fm %.3fm %.3fm" % (mano["x"], mano["y"] - 0.03, mano["z"]),
                "0deg 84deg 1.10m",
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
