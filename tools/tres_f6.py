"""F: fija los numeros del caso elegido y los pasa a la forma limpia del catalogo.

El barrido trabajaba con rotaciones extra en la raiz de cada dedo, pero el
`spread` del catalogo gira ese mismo hueso en ese mismo eje, asi que las dos
formas deben dar la misma mano: se mide una y otra y se comparan antes de
escribir nada. Tambien se comprueba que la pinza de la letra sigue cerrada, que
es lo que `nudillos` se puede llevar por delante al mover la raiz del indice.
"""
import json
import time

from playwright.sync_api import sync_playwright

from lab_e2 import abrir, preparar
from tres_f import BASE, TRES_JS, informe
from tres_f3 import pose
from tres_f5 import paralelos

NUDILLOS = 0.28
CIERRE = 8


def main():
    with sync_playwright() as p:
        browser, page = abrir(p)
        preparar(page)

        z = paralelos(page, NUDILLOS, CIERRE)
        print("grados de z resueltos:", {k: round(v, 2) for k, v in z.items()})

        con_extra = pose(NUDILLOS, z["Middle"], z["Ring"], z["Pinky"])
        page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", con_extra)
        time.sleep(0.25)
        m1 = page.evaluate(TRES_JS)
        print(informe("con extra", m1))

        # misma cosa metida en el spread: es el mismo hueso y el mismo eje
        limpia = {
            "thumb": dict(BASE["thumb"]),
            "index": dict(BASE["index"]),
            "middle": {"curl": 0.0, "spread": round(3 + z["Middle"])},
            "ring": {"curl": 0.0, "spread": round(4 + z["Ring"])},
            "pinky": {"curl": 0.0, "spread": round(6 + z["Pinky"])},
            "nudillos": NUDILLOS,
            "extra": {"RightHandThumb1": {"z": 50}},
        }
        page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", limpia)
        time.sleep(0.25)
        m2 = page.evaluate(TRES_JS)
        print(informe("con spread", m2))

        difs = {
            "medio-anular": abs(m1["mr"]["distal"] - m2["mr"]["distal"]),
            "anular-menique": abs(m1["rp"]["distal"] - m2["rp"]["distal"]),
            "pinza": abs(m1["pinza"] - m2["pinza"]),
        }
        print("diferencia entre las dos formas:", {k: round(v, 4) for k, v in difs.items()})
        print("las dos formas dan la misma mano:", max(difs.values()) < 0.004)
        print("\npose para el catalogo:\n" + json.dumps(limpia, indent=2, ensure_ascii=False))
        browser.close()


if __name__ == "__main__":
    main()
