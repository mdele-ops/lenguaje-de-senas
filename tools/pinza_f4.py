"""F: barrido fino de la pinza y retrato de los finalistas.

Se busca contacto en la punta (0.04-0.08 palmas entre los huesos de punta, que
es donde la piel se toca sin hundirse), falanges distales enfrentadas y el
pulgar lo mas vertical posible, que es como describe la letra el catalogo.
"""
import itertools
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from junta_f import PINZA_JS
from lab_e2 import MARCO_JS, abrir, hoja, orbita, preparar, recorte
from pinza_f3 import PUNTO_JS, VISTAS, encuadrar, pose

OUT = Path(__file__).resolve().parents[1] / "tools" / "screenshots" / "pinza_f4"

REJILLA = list(
    itertools.product(
        (0.40, 0.45, 0.50, 0.55),        # curl pulgar
        (-0.3, -0.2, -0.1, 0.0),         # aside pulgar
        (0.52, 0.55, 0.58, 0.61),        # curl indice
        (12, 14, 16, 18),                # spread indice
        (45, 50, 55),                    # z extra del trapecio
    )
)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser, page = abrir(p)
        viewer = preparar(page)

        buenos = []
        for i, combo in enumerate(REJILLA):
            page.evaluate(
                "(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose(*combo)
            )
            m = page.evaluate(PINZA_JS)
            if i % 96 == 0:
                print(f"  {i}/{len(REJILLA)}")
            if not (0.040 <= m["puntas"] <= 0.080):
                continue
            if m["enfrentados"] < 85 or min(m["dondeT"], m["dondeI"]) < 0.95:
                continue
            buenos.append((-m["pulgarArriba"], combo, m))

        buenos.sort(key=lambda f: f[0])
        print(f"{len(buenos)} poses con contacto en la punta; mejores por pulgar vertical:")
        for _, combo, m in buenos[:14]:
            tc, ta, ic, isp, t1z = combo
            print(
                f"  tc{tc} ta{ta} ic{ic} sp{isp} z{t1z} puntas={m['puntas']:.3f} "
                f"yemas={m['yemas']:.3f} enfrent={m['enfrentados']:.0f} "
                f"vertical={m['pulgarArriba']:+.2f} alto T/I={m['altoT']:+.2f}/{m['altoI']:+.2f}"
            )

        salida = {}
        for _, combo, m in buenos[:6]:
            tc, ta, ic, isp, t1z = combo
            nombre = f"tc{tc}_ta{ta}_ic{ic}_sp{isp}_z{t1z}_p{m['puntas']:.3f}"
            page.evaluate(
                "(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose(*combo)
            )
            time.sleep(0.3)
            marco = page.evaluate(MARCO_JS)
            c = page.evaluate(PUNTO_JS)
            t = "%.4fm %.4fm %.4fm" % (c["x"], c["y"], c["z"])
            for vista, pesos in VISTAS.items():
                encuadrar(page, orbita(marco, pesos, radio_palmas=2.4), "16deg", t)
                salida.setdefault(vista, []).append(
                    (nombre, recorte(page, viewer, OUT / f"{nombre}_{vista}.png"))
                )
            # y la mano entera, para no perder de vista la forma de la letra
            encuadrar(page, orbita(marco, (1.0, 0.0, -0.2), radio_palmas=4.6), "24deg",
                      "%.4fm %.4fm %.4fm" % (marco["centro"]["x"], marco["centro"]["y"],
                                             marco["centro"]["z"]))
            salida.setdefault("mano", []).append(
                (nombre, recorte(page, viewer, OUT / f"{nombre}_mano.png"))
            )
        browser.close()

    for vista, imgs in salida.items():
        print("hoja:", hoja(imgs, OUT / f"_{vista}.png", cols=3, cell=340))


if __name__ == "__main__":
    main()
