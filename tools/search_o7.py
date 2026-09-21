"""O, paso 7: elegir el pulgar. En la foto el pulgar va casi recto subiendo por
el costado y solo la yema gira para tocar el indice; con tcurl alto quedaba
demasiado doblado y metido, y el hueco de la O dejaba de leerse.
"""
from playwright.sync_api import sync_playwright

import lsm_lab as L

OUT = L.out_dir("search_o7")

FINGERS = {"conv": -27, "c": 0.60, "k": 28, "m2": -10, "d3": -34}

# Candidatos de pulgar salidos del paso 4, de mas recto a mas doblado.
THUMBS = {
    "A_t30": {"tcurl": 0.30, "taside": 0.25, "t1y": -15, "t1z": 30, "t2x": 5, "t3x": 30},
    "B_t45": {"tcurl": 0.45, "taside": 0.25, "t1y": -15, "t1z": 30, "t2x": 5, "t3x": 30},
    "C_t45b": {"tcurl": 0.45, "taside": 1.00, "t1y": -40, "t1z": 30, "t2x": 5, "t3x": 30},
    "D_t60": {"tcurl": 0.60, "taside": 0.00, "t1y": -40, "t1z": 0, "t2x": 5, "t3x": 10},
    "E_t60b": {"tcurl": 0.60, "taside": 0.50, "t1y": -40, "t1z": 15, "t2x": 5, "t3x": 10},
    "F_t75": {"tcurl": 0.75, "taside": 0.25, "t1y": -40, "t1z": 15, "t2x": -15, "t3x": 30},
    "G_t90": {"tcurl": 0.90, "taside": 0.00, "t1y": -40, "t1z": 0, "t2x": -35, "t3x": 30},
}

WY = [0, 15]


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", args=L.CHROME_ARGS)
        page = L.open_ready_page(browser, viewport=(1100, 900))
        viewer = page.query_selector("#viewer")

        for label, thumb in THUMBS.items():
            for wy in WY:
                params = {**FINGERS, **thumb}
                pose = L.pose_from_params(params)
                pose["muneca"] = {"y": wy}
                L.apply_pose(page, pose)
                m = L.measure(page)
                print(
                    f"{label:8s} wy={wy:3d}  dI={m['dI']:.2f} dM={m['dM']:.2f} "
                    f"reach={m['reach']:.2f} hole={m['hole']:.2f}"
                )
                L.set_camera(page, orbit="0deg 82deg 0.40m", fov="25deg")
                viewer.screenshot(path=str(OUT / f"{label}_wy{wy:02d}.png"))

        browser.close()
        print("->", OUT)


if __name__ == "__main__":
    main()
