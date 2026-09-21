"""Regresion alrededor de la S: que siga distinguiendose de las otras de puno.

A, E, M, N, S y T son todas la misma mano cerrada y lo unico que las separa es
donde queda el pulgar. Por eso arreglar la S es justo el cambio con mas riesgo
de dejar dos letras iguales, y por eso conviene mirarlas juntas:

  A  pulgar de pie al costado del indice, sin cruzar        (camU ~ 0)
  S  pulgar tumbado cruzando por delante de los dedos       (camU alto)
  T  pulgar metido entre indice y medio
  E  yemas apoyadas sobre el pulgar atravesado
  M/N dedos colgando, pulgar sujetandolos

Se aplican desde el catalogo real (mostrarSena, con su transicion) y se exige
que solo la S cruce por delante y que la S quede lejos de todas las demas.

Dos cosas que NO son fallo aunque lo parezcan, y por eso estan exceptuadas:
la E apoya las yemas encima del pulgar a proposito, asi que su hueco pulgar-dedo
es pequeno por diseno; y M y N llevan el mismo pulgar porque lo que las separa
es cuantos dedos cuelgan, no donde va el pulgar.
"""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from enfoque_r import MANO, captura, hoja
from eje_r import CAM_FOV, CAM_ORBIT, CAM_TARGET, cam
from pose_lab_e import free_camera
from pose_lab_s import MEASURE_JS
import search_e9 as se9
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "verify_vecinas_s"
OUT.mkdir(parents=True, exist_ok=True)

se9.URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=vecs"

LETRAS = ["A", "E", "M", "N", "T", "S"]

# La S cruza por delante y se apoya; el resto no debe hacerlo.
CRUZA_U = 0.45
CRUZA_FRENTE = 0.08
GAP_MIN = 0.100
SIN_HUECO = {"E"}          # la E lleva las yemas apoyadas sobre el pulgar
SEPARACION_MIN = 0.20      # cuanto tiene que alejarse la S de cada vecina


def main():
    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 1000, "height": 1000})
        time.sleep(0.3)
        free_camera(page)
        cam(page, CAM_TARGET, CAM_ORBIT, CAM_FOV)

        total = page.evaluate(
            "() => window.__LSM_CONTROLLER__.getCatalog().senas.length"
        )
        print("senas en el catalogo:", total)

        items, fallos, huella = [], [], {}
        for letra in LETRAS:
            r = page.evaluate("(l) => window.__LSM_CONTROLLER__.mostrarSena(l)", letra)
            time.sleep(2.5)
            cam(page, CAM_TARGET, CAM_ORBIT, CAM_FOV)
            m = page.evaluate(MEASURE_JS)
            cruza = m["camU"] > CRUZA_U and m["sobreFrente"] > CRUZA_FRENTE
            print(
                f"{letra:2s} modo={r['modo']:8s} camU={m['camU']:+5.2f} "
                f"sobreFrente={m['sobreFrente']:+6.3f} camAlt={m['camAlt']:+5.2f} "
                f"gap={m['gapDedos']:.3f} lat={m['thLatDir']:+5.2f} "
                f" {'CRUZA' if cruza else '-'}"
            )

            if cruza != (letra == "S"):
                fallos.append(f"{letra}: cruce {m['camU']:+.2f}/{m['sobreFrente']:+.3f}")
            if letra not in SIN_HUECO and m["gapDedos"] < GAP_MIN:
                fallos.append(f"{letra}: pulgar dentro del dedo (gap {m['gapDedos']:.3f})")
            huella[letra] = (m["camU"], m["camAlt"])

            ruta = OUT / f"{letra}.png"
            captura(page, ruta, MANO, margen=0.28, lado=460)
            items.append((letra, ruta))

        browser.close()

    # la S no puede acabar con el pulgar donde lo tiene otra letra de puno
    for otra in (l for l in huella if l != "S"):
        d = max(abs(huella["S"][k] - huella[otra][k]) for k in (0, 1))
        if d < SEPARACION_MIN:
            fallos.append(f"S y {otra} tienen el pulgar en el mismo sitio ({d:.2f})")

    hoja(items, OUT / "_vecinas.png", cols=6, cell=320, titulo="S y las de puno")
    print("\n  " + ("TODO OK" if not fallos else "REVISAR: " + "; ".join(fallos)))


if __name__ == "__main__":
    main()
