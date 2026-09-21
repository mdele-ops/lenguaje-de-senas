"""S lab 11: que eje pega el pulgar contra los dedos.

Las tres busquedas anteriores cruzan bien el pulgar de frente, pero de perfil
se ve que va por el aire: la yema queda a 0.40 palmas por delante del punto mas
adelantado del puno (sobreFrente), cuando para apoyarse deberia estar en torno
a 0.15, que es lo que abultan pulgar y dedo juntos.

Ninguna combinacion de la rejilla bajaba de 0.35, asi que el problema no es
afinar: es que ningun eje de los que estaba moviendo mete el pulgar hacia
dentro. Este lab mueve UNO cada vez, con margen amplio, partiendo de la mejor
candidata, y mira solo dos numeros:

  sobreFrente  la yema por delante del frente del puno. Hay que bajarlo.
  gapDedos     distancia pulgar-dedos. Como los huesos van por el centro de la
               carne, apoyarse sin atravesarse es ~0.15-0.25; por debajo de
               0.12 la malla del pulgar ya se mete en la del dedo.
"""
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from pose_lab_e import T1, T2, T3, free_camera
from pose_lab_s import MEASURE_JS
from search_s2 import puno_s
from ver_s import cam
import search_e9 as se9
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "eje_s"
OUT.mkdir(parents=True, exist_ok=True)

se9.URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=s11"

BASE = dict(tcurl=0.25, t1={"x": 0, "y": -30, "z": 10}, t2={"x": 40}, t3={})


def arma(tcurl, t1, t2, t3):
    thumb = {T1: dict(t1), T2: dict(t2)}
    if t3:
        thumb[T3] = dict(t3)
    return puno_s(tcurl=tcurl, thumb=thumb)


def linea(nombre, m):
    return (
        f"{nombre:16s} sobreFrente={m['sobreFrente']:+6.3f} gap={m['gapDedos']:.3f} "
        f"camU={m['camU']:+5.2f} camAlt={m['camAlt']:+5.2f} "
        f"camCima={m['camCima']:+5.2f} lat={m['thLatDir']:+5.2f} "
        f"up={m['thUpDir']:+5.2f} apoyoMed={m['apoyoMed']:.3f}"
    )


def casos():
    yield "base", arma(**BASE)
    for eje in ("x", "y", "z"):
        for g in (-60, -40, -20, 20, 40, 60):
            for hueso, clave in ((T1, "t1"), (T2, "t2"), (T3, "t3")):
                kw = {k: dict(v) if isinstance(v, dict) else v
                      for k, v in BASE.items()}
                kw[clave] = dict(kw[clave])
                kw[clave][eje] = kw[clave].get(eje, 0) + g
                nombre = f"{clave.upper()}_{eje}{g:+d}"
                yield nombre, arma(**kw)
    for tc in (0.0, 0.5, 0.75, 1.0):
        kw = {k: dict(v) if isinstance(v, dict) else v for k, v in BASE.items()}
        kw["tcurl"] = tc
        yield f"tcurl_{tc}", arma(**kw)


def main():
    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 1000, "height": 1000})
        time.sleep(0.4)
        free_camera(page)
        cam(page, "0deg 84deg 2.5m")

        medidas = {}
        for nombre, pose in casos():
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
            time.sleep(0.13)
            m = page.evaluate(MEASURE_JS)
            medidas[nombre] = m
            print(" ", linea(nombre, m))

        browser.close()

    (OUT / "_medidas.json").write_text(json.dumps(medidas, indent=2), "utf-8")
    print("\nDatos en", OUT)


if __name__ == "__main__":
    main()
