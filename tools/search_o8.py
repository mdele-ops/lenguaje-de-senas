"""O, paso 8: barrido fino de orientacion con encuadre cerrado.

Busca el punto donde, de frente, la mano sigue compacta (como en la foto) pero
ya se ve el hueco de la O entre el pulgar y los dedos.
"""
from playwright.sync_api import sync_playwright

import lsm_lab as L

OUT = L.out_dir("search_o8")

FINGERS = {"conv": -27, "c": 0.60, "k": 28, "m2": -10, "d3": -34}
# pulgar D del paso 7: dI=0.05 con el hueco mas grande (0.55)
THUMB = {"tcurl": 0.60, "taside": 0.00, "t1y": -40, "t1z": 0, "t2x": 5, "t3x": 10}

WY = [20, 28, 36, 44, 52, 60]


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", args=L.CHROME_ARGS)
        page = L.open_ready_page(browser, viewport=(1100, 900))
        viewer = page.query_selector("#viewer")

        for wy in WY:
            pose = L.pose_from_params({**FINGERS, **THUMB})
            pose["muneca"] = {"y": wy}
            L.apply_pose(page, pose)
            L.set_camera(page, orbit="0deg 82deg 0.30m", fov="20deg")
            viewer.screenshot(path=str(OUT / f"wy{wy:03d}.png"))
            print("wy", wy)

        browser.close()
        print("->", OUT)


if __name__ == "__main__":
    main()
