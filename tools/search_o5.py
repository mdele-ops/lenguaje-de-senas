"""O, paso 5: orientar el circulo hacia la camara frontal de produccion.

La forma de la mano ya esta (pasos 3 y 4), pero el plano de la O apuntaba unos
40 grados a un lado: de frente se leia como garra. Aqui se barre la rotacion de
muneca y se renderiza con el encuadre real de practica.html.
"""
import itertools

from playwright.sync_api import sync_playwright

import lsm_lab as L

OUT = L.out_dir("search_o5")

# Forma ganadora de los pasos 3 y 4 (arco compacto + pulgar en contacto).
SHAPE = {
    "conv": -27, "c": 0.60, "k": 28, "m2": -10, "d3": -34,
    "tcurl": 0.90, "taside": 0.0, "t1y": -40, "t1z": 0, "t2x": -35, "t3x": 30,
}

WY = [10, 30, 50, 70, 90, 110]
WZ = [-20, 0, 20]

# Encuadre real de la pagina (rig.cameraTarget / rig.cameraOrbit del catalogo).
PROD_TARGET = "0m 2.45m 0.15m"
PROD_ORBIT = "0deg 84deg 2.5m"


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", args=L.CHROME_ARGS)
        page = L.open_ready_page(browser, viewport=(1100, 900))
        viewer = page.query_selector("#viewer")

        for wy, wz in itertools.product(WY, WZ):
            pose = L.pose_from_params(SHAPE)
            pose["muneca"] = {"y": wy, "z": wz}
            L.apply_pose(page, pose)
            m = L.measure(page)
            print(f"wy={wy:4d} wz={wz:+4d}  dI={m['dI']:.2f} reach={m['reach']:.2f}")

            # cerca, para juzgar la forma
            L.set_camera(page, orbit="0deg 82deg 0.42m", fov="26deg")
            viewer.screenshot(path=str(OUT / f"wy{wy:03d}_wz{wz:+03d}_cerca.png"))

        # y una tira con el encuadre de produccion
        prod = L.out_dir("search_o5_prod")
        for wy, wz in itertools.product(WY, WZ):
            pose = L.pose_from_params(SHAPE)
            pose["muneca"] = {"y": wy, "z": wz}
            L.apply_pose(page, pose)
            L.set_camera(page, target=PROD_TARGET, orbit=PROD_ORBIT, fov="30deg")
            viewer.screenshot(path=str(prod / f"wy{wy:03d}_wz{wz:+03d}.png"))

        browser.close()
        print("->", OUT)


if __name__ == "__main__":
    main()
