"""O, paso 6: barrido fino de muneca alrededor de wy=10, que es donde de frente
la mano se lee compacta como en la foto (nudillos arriba, pulgar a la derecha).
"""
import itertools

from playwright.sync_api import sync_playwright

import lsm_lab as L

OUT = L.out_dir("search_o6")

SHAPE = {
    "conv": -27, "c": 0.60, "k": 28, "m2": -10, "d3": -34,
    "tcurl": 0.90, "taside": 0.0, "t1y": -40, "t1z": 0, "t2x": -35, "t3x": 30,
}

WY = [-15, 0, 15, 30]
WZ = [-15, 0, 15]
WX = [0, 20]


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", args=L.CHROME_ARGS)
        page = L.open_ready_page(browser, viewport=(1100, 900))
        viewer = page.query_selector("#viewer")

        for wx, wy, wz in itertools.product(WX, WY, WZ):
            pose = L.pose_from_params(SHAPE)
            pose["muneca"] = {"x": wx, "y": wy, "z": wz}
            L.apply_pose(page, pose)
            L.set_camera(page, orbit="0deg 82deg 0.40m", fov="25deg")
            viewer.screenshot(
                path=str(OUT / f"x{wx:+03d}_y{wy:+03d}_z{wz:+03d}.png")
            )
            print(f"wx={wx:+3d} wy={wy:+3d} wz={wz:+3d}")

        browser.close()
        print("->", OUT)


if __name__ == "__main__":
    main()
