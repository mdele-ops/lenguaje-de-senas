"""O, paso 1: encontrar el 'spread' que junta los dedos.

En la referencia los cuatro dedos van pegados formando un solo arco. Aqui se
barre un parametro de convergencia (los dedos se abren en abanico segun su
posicion) y se mide la separacion entre yemas vecinas.
"""
from playwright.sync_api import sync_playwright

import lsm_lab as L

OUT = L.out_dir("lab_o_juntar")


def conv_spread(c):
    """c>0 abre el abanico, c<0 lo cierra; el indice y el menique son los extremos."""
    return (-1.5 * c, -0.5 * c, 0.5 * c, 1.5 * c)


CASES = {}
CASES["00_actual"] = L.build_pose()
for c in (-8, -4, 0, 4, 8, 12):
    CASES[f"conv_{c:+03d}"] = L.build_pose(spread=conv_spread(c))


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", args=L.CHROME_ARGS)
        page = L.open_ready_page(browser)
        viewer = page.query_selector("#viewer")

        print(f"{'caso':12s} {'dI':>5s}{'dM':>6s}{'dR':>6s}{'dP':>6s}  "
              f"{'gIM':>6s}{'gMR':>6s}{'gRP':>6s}  suma_huecos")
        for name, pose in CASES.items():
            L.apply_pose(page, pose)
            m = L.measure(page)
            gaps = m["gIM"] + m["gMR"] + m["gRP"]
            print(
                f"{name:12s} {m['dI']:5.2f}{m['dM']:6.2f}{m['dR']:6.2f}{m['dP']:6.2f}  "
                f"{m['gIM']:6.2f}{m['gMR']:6.2f}{m['gRP']:6.2f}  {gaps:6.2f}"
            )
            # angulo donde hoy se lee mejor el circulo
            L.set_camera(page, orbit="-40deg 82deg 0.42m")
            viewer.screenshot(path=str(OUT / f"{name}.png"))

        browser.close()
        print("->", OUT)


if __name__ == "__main__":
    main()
