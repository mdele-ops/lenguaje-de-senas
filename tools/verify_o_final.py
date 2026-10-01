"""Verificacion de la letra O tal como queda en produccion.

No aplica poses de prueba: llama a mostrarSena('O') igual que el boton de la
pagina, espera la transicion y mide/captura el resultado real del catalogo.
"""
import time

from playwright.sync_api import sync_playwright

import lsm_lab as L

OUT = L.out_dir("verify_o_final")


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", args=L.CHROME_ARGS)
        page = L.open_ready_page(browser, viewport=(1100, 900))
        viewer = page.query_selector("#viewer")

        info = page.evaluate(
            """() => {
                const c = window.__LSM_CONTROLLER__;
                const r = c.mostrarSena('O');
                const s = c.getSena('O');
                return { modo: r.modo, version: c.getCatalog().version,
                         descripcion: s.descripcion };
            }"""
        )
        print("modo        :", info["modo"])
        print("version     :", info["version"])
        print("descripcion :", info["descripcion"])

        # la transicion del catalogo dura 2 s
        time.sleep(2.6)

        m = L.measure(page)
        print(
            "\nmedidas (normalizadas al largo de la palma):\n"
            f"  yema->pulgar   I={m['dI']:.2f} M={m['dM']:.2f} "
            f"R={m['dR']:.2f} P={m['dP']:.2f}\n"
            f"  dedos juntos   {m['gIM']:.2f}/{m['gMR']:.2f}/{m['gRP']:.2f}\n"
            f"  mano recogida  reach={m['reach']:.2f}   hueco={m['hole']:.2f}"
        )

        caption = page.evaluate(
            "() => (document.getElementById('anim-info')||{}).textContent"
        )
        print("rotulo      :", caption)

        L.set_camera(page, orbit="0deg 82deg 0.30m", fov="20deg")
        viewer.screenshot(path=str(OUT / "frente.png"))
        L.set_camera(page, orbit="-45deg 82deg 0.34m", fov="22deg")
        viewer.screenshot(path=str(OUT / "tres_cuartos.png"))
        L.set_camera(page, orbit="-90deg 82deg 0.36m", fov="22deg")
        viewer.screenshot(path=str(OUT / "perfil.png"))
        L.set_camera(
            page, target="0m 2.45m 0.15m", orbit="0deg 84deg 2.5m", fov="30deg"
        )
        viewer.screenshot(path=str(OUT / "produccion.png"))

        browser.close()
        print("->", OUT)


if __name__ == "__main__":
    main()
