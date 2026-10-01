"""Compara con la misma camara la O anterior del catalogo y la nueva."""
from playwright.sync_api import sync_playwright

import lsm_lab as L

OUT = L.out_dir("antes_despues_o")

# Pose que tenia el catalogo antes de este ajuste (version 1.3.38).
ANTES = {
    "thumb": {"curl": 0.46, "aside": 0.36},
    "index": {"curl": 0.5, "spread": -4},
    "middle": {"curl": 0.5, "spread": 3},
    "ring": {"curl": 0.5, "spread": 4},
    "pinky": {"curl": 0.5, "spread": 6},
    "muneca": {"y": 50},
    "extra": {
        "mixamorig1RightHandIndex1_040": {"x": 12},
        "mixamorig1RightHandMiddle1_044": {"x": 12},
        "mixamorig1RightHandRing1_048": {"x": 12},
        "mixamorig1RightHandPinky1_052": {"x": 12},
        "mixamorig1RightHandThumb1_036": {"y": 0, "z": 28},
        "mixamorig1RightHandThumb2_037": {"x": -28},
        "mixamorig1RightArm_033": {"z": -18},
    },
}

VISTAS = {
    "frente": ("0deg 82deg 0.30m", "20deg"),
    "tres_cuartos": ("-45deg 82deg 0.34m", "22deg"),
}


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", args=L.CHROME_ARGS)
        page = L.open_ready_page(browser, viewport=(1100, 900))
        viewer = page.query_selector("#viewer")

        despues = page.evaluate("() => window.__LSM_CONTROLLER__.getSena('O').pose")

        for etiqueta, pose in (("antes", ANTES), ("despues", despues)):
            L.apply_pose(page, pose)
            m = L.measure(page)
            print(
                f"{etiqueta:8s} yema->pulgar I={m['dI']:.2f} P={m['dP']:.2f} | "
                f"dedos juntos {m['gIM']:.2f}/{m['gMR']:.2f}/{m['gRP']:.2f} | "
                f"reach={m['reach']:.2f}"
            )
            for vista, (orbit, fov) in VISTAS.items():
                L.set_camera(page, orbit=orbit, fov=fov)
                viewer.screenshot(path=str(OUT / f"{vista}_{etiqueta}.png"))

        browser.close()
        print("->", OUT)


if __name__ == "__main__":
    main()
