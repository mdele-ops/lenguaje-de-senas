"""O, paso final: arma la pose elegida, la valida desde todos los angulos e
imprime el JSON listo para pegar en data/catalogo-lsm.json.
"""
import json

from playwright.sync_api import sync_playwright

import lsm_lab as L

OUT = L.out_dir("final_o")

PARAMS = {
    # arco compacto: los 4 dedos juntos, nudillos muy doblados y yema plana
    "conv": -27, "c": 0.60, "k": 28, "m2": -10, "d3": -34,
    # pulgar casi recto que sube por el costado y toca la yema del indice
    "tcurl": 0.60, "taside": 0.00, "t1y": -40, "t1z": 0, "t2x": 5, "t3x": 10,
    # el plano del circulo mira al frente lo justo para que se vea el hueco
    "wy": 30,
}


def main():
    pose = L.pose_from_params(PARAMS)
    print("pose para el catalogo:")
    print(json.dumps(pose, indent=2, ensure_ascii=False))

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", args=L.CHROME_ARGS)
        page = L.open_ready_page(browser, viewport=(1100, 900))
        viewer = page.query_selector("#viewer")

        L.apply_pose(page, pose)
        m = L.measure(page)
        print(
            "\nmedidas (normalizadas al largo de la palma):\n"
            f"  yema->pulgar   I={m['dI']:.2f} M={m['dM']:.2f} "
            f"R={m['dR']:.2f} P={m['dP']:.2f}\n"
            f"  dedos juntos   {m['gIM']:.2f}/{m['gMR']:.2f}/{m['gRP']:.2f}\n"
            f"  mano recogida  reach={m['reach']:.2f}   hueco={m['hole']:.2f}"
        )

        # vuelta completa para descartar cruces o dedos atravesados
        for theta in range(-120, 121, 30):
            L.set_camera(page, orbit=f"{theta}deg 82deg 0.34m", fov="22deg")
            viewer.screenshot(path=str(OUT / f"giro_{theta:+04d}.png"))

        # vista de frente, la que usa la pagina
        L.set_camera(page, orbit="0deg 82deg 0.30m", fov="20deg")
        viewer.screenshot(path=str(OUT / "frente.png"))

        prod = L.out_dir("final_o_prod")
        L.set_camera(page, target="0m 2.45m 0.15m", orbit="0deg 84deg 2.5m", fov="30deg")
        viewer.screenshot(path=str(prod / "produccion.png"))

        browser.close()
        print("->", OUT)


if __name__ == "__main__":
    main()
