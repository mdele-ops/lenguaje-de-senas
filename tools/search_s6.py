"""S lab 14: ajuste fino alrededor de la zona buena.

El lab 13 da ya la S: el pulgar cruza por delante y se apoya (sobreFrente 0.15,
gap 0.16-0.19, y de perfil deja de sobresalir). Quedan dos detalles contra la
lamina:

  - la yema se pasa de largo, casi hasta el canto del menique (camU ~0.78);
    en la lamina para sobre el medio/anular
  - cruza demasiado empinado; el pulgar de la lamina va mas tumbado

Asi que se busca fino en ese entorno con camU y thUpDir apretados. apoyoIdx sale
del coste a proposito: en cuanto el pulgar cruza por delante del indice la yema
se aleja de el por definicion, y penalizarlo empujaba la pose hacia atras.
"""
import itertools
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from enfoque_r import MANO, captura, hoja
from pose_lab_e import T1, T2, free_camera
from pose_lab_s import MEASURE_JS
from search_s2 import puno_s
from ver_s import VISTAS, cam
import search_e9 as se9
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "search_s6"
OUT.mkdir(parents=True, exist_ok=True)
REF = ROOT / "tools" / "screenshots" / "final_s" / "_ref.png"

se9.URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=s14"

GAP_MIN = 0.130

OBJETIVO = {
    "sobreFrente": (0.17, 12.0),
    "camU": (0.58, 8.0),
    "camAlt": (-0.20, 3.0),
    "gapDedos": (0.19, 8.0),
    "apoyoMed": (0.20, 5.0),
    "thLatDir": (0.80, 3.0),
    "thUpDir": (0.10, 3.0),
}


def puntua(m):
    if m.get("error") or "camU" not in m:
        return 9e9
    coste = sum(p * abs(m[k] - ideal) for k, (ideal, p) in OBJETIVO.items())
    if m["gapDedos"] < GAP_MIN:
        coste += 60 * (GAP_MIN - m["gapDedos"]) / GAP_MIN
    if m["sobreFrente"] < 0.04:
        coste += 40
    if m["camCima"] > -0.04:
        coste += 25 * (m["camCima"] + 0.04)
    return coste


def arma(tc, z, y, x, t2x, t2y):
    return puno_s(
        tcurl=tc, thumb={T1: {"x": x, "y": y, "z": z}, T2: {"x": t2x, "y": t2y}}
    )


def candidatas():
    for tc, z, y, x, t2x, t2y in itertools.product(
        (0.3, 0.4),
        (-10, 0, 10),
        (-95, -85, -75),
        (20, 30, 40),
        (30, 45, 60),
        (-25, 0),
    ):
        yield f"c{tc}_z{z}_y{y}_x{x}_t{t2x}_{t2y}", arma(tc, z, y, x, t2x, t2y)


def linea(nombre, m):
    return (
        f"{nombre:28s} sobre={m['sobreFrente']:+6.3f} gap={m['gapDedos']:.3f} "
        f"apM={m['apoyoMed']:.3f} camU={m['camU']:+5.2f} "
        f"camAlt={m['camAlt']:+5.2f} camCima={m['camCima']:+5.2f} "
        f"lat={m['thLatDir']:+5.2f} up={m['thUpDir']:+5.2f}"
    )


def main():
    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 1100, "height": 1100})
        time.sleep(0.4)
        free_camera(page)
        cam(page, "0deg 84deg 2.5m")

        res = []
        for nombre, pose in candidatas():
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
            time.sleep(0.12)
            m = page.evaluate(MEASURE_JS)
            res.append({"nombre": nombre, "coste": puntua(m), "m": m, "pose": pose})

        res.sort(key=lambda r: r["coste"])
        print("mejores:")
        for r in res[:12]:
            print(f"  {r['coste']:7.3f}  {linea(r['nombre'], r['m'])}")

        items = [("REF lamina", REF)] if REF.exists() else []
        for r in res[:6]:
            page.evaluate(
                "(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", r["pose"]
            )
            time.sleep(0.3)
            for vista, orbit in VISTAS:
                ruta = OUT / f"{r['nombre']}_{vista}.png"
                cam(page, orbit)
                captura(page, ruta, MANO, margen=0.26, lado=460)
                items.append((f"{r['nombre'][:22]} {vista}", ruta))

        browser.close()

    hoja(items, OUT / "_hoja.png", cols=4, cell=380, titulo="S · fino")
    (OUT / "_top.json").write_text(
        json.dumps([{k: r[k] for k in ("nombre", "coste", "m", "pose")}
                    for r in res[:20]], indent=2),
        "utf-8",
    )
    print("Capturas en", OUT)


if __name__ == "__main__":
    main()
