"""Estado actual de la H: medidas y tres vistas, contra el reposo y contra la U."""
from pathlib import Path

from playwright.sync_api import sync_playwright

import h_lab
import lab

OUT = h_lab.SHOTS / "estado_h"


def main():
    catalog = lab.load_catalog()
    senas = {s["letra"]: s for s in catalog["senas"]}
    casos = {
        "reposo": {"thumb": {"curl": 0}, "index": {"curl": 0}, "middle": {"curl": 0},
                   "ring": {"curl": 0}, "pinky": {"curl": 0}},
        "H_actual": senas["H"]["pose"],
        "U_actual": senas["U"]["pose"],
    }

    with sync_playwright() as p:
        browser, page = h_lab.abre(p, catalog)
        items = []
        for nombre, pose in casos.items():
            lab.apply_pose(page, pose)
            m = h_lab.metricas(page)
            print(
                f"{nombre}: yemas_ind_med={m['yemas_ind_med']:5.1f}mm "
                f"nud_ind_med={m['nud_ind_med']:5.1f}mm "
                f"ancho_nudillos={m['ancho_nudillos']:5.1f}mm "
                f"largo_indice={m['largo_indice']:5.1f}mm "
                f"largo_palma={m['largo_palma']:5.1f}mm "
                f"pulgar_alto={m['pulgar_alto']:+6.1f}mm",
                flush=True,
            )
            items.extend(h_lab.fotos(page, OUT, nombre))
        browser.close()

    h_lab.hoja(items, OUT / "_hoja.png", cols=3, cell=320)


if __name__ == "__main__":
    main()
