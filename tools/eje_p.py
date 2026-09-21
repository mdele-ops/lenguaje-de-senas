"""Barrido de un solo eje: que rotacion de muñeca inclina la mano EN PANTALLA.

El controlador aplica las rotaciones de `muneca` en orden x, y, z sobre el
hueso, asi que cada eje actua en un marco distinto y no se puede adivinar cual
inclina la mano dentro del plano de la pantalla sin medirlo. Se busca el eje
que mueva idxAng/midAng dejando quietos palmNz (perfil) e idxScr/midScr
(largo aparente).
"""
import time

from playwright.sync_api import sync_playwright

from pose_lab_p7 import CAM_FOV, CAM_ORBIT, CAM_TARGET
from pose_lab_p9 import MEASURE_JS, pose_p9
import search_e9 as se9
from search_e9 import abrir

se9.URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=eje"


def barrido(page, titulo, hacer):
    print(titulo)
    for v in (-45, -30, -15, 0, 15, 30, 45, 60):
        page.evaluate(
            "(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", hacer(v)
        )
        m = page.evaluate(MEASURE_JS)
        print(
            f"  {v:+4d}  idxAng={m['idxAng']:+7.1f} midAng={m['midAng']:+7.1f} "
            f"esc={m['escuadra']:5.1f} palmNz={m['palmNz']:+.2f} "
            f"idxScr={m['idxScr']:.2f} midScr={m['midScr']:.2f} "
            f"mano={m['manoAng']:+6.1f} brazo={m['brazoAng']:+6.1f}"
        )
    print()


def main():
    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 1100, "height": 900})
        time.sleep(0.5)
        page.evaluate(
            """(a) => {
                const mv = document.getElementById('handViewer');
                mv.cameraTarget = a.t;
                mv.cameraOrbit = a.orbit;
                mv.fieldOfView = a.fov;
                mv.jumpCameraToGoal();
            }""",
            {"t": CAM_TARGET, "orbit": CAM_ORBIT, "fov": CAM_FOV},
        )
        time.sleep(0.4)

        # El controlador aplica primero pose.muneca y DESPUES pose.extra sobre
        # el mismo hueso, asi que un extra en la muñeca gira sobre la mano ya
        # colocada de perfil: ahi si cae el eje de los nudillos, que es el que
        # dobla la mano dentro del plano de la pantalla.
        def con_extra(eje, v):
            pose = pose_p9(mid_mcp=90, wy=95, wz=0, wx=0)
            pose["extra"]["mixamorig1RightHand_035"] = {eje: v}
            return pose

        for eje in ("x", "y", "z"):
            barrido(page, f"extra muñeca {eje} (despues del giro de perfil):",
                    lambda v, e=eje: con_extra(e, v))

        browser.close()


if __name__ == "__main__":
    main()
