"""S lab 13: buscar donde el lab 11 dijo que estaba la solucion.

El lab 12 volvio a quedarse con el pulgar por el aire (sobreFrente ~0.45) y la
razon es tonta: barria T1.y entre -15 y -45, pero en el lab 11 los valores que
metian el pulgar contra el puno eran los de la punta del barrido, y ahi la y
efectiva era -70 y -90, no -45. O sea que la rejilla no llegaba a la zona
buena.

Aqui se busca en esa zona y se puntua el apoyo donde importa: no basta con que
la cadena del pulgar roce el puno en algun punto (eso lo cumple tocando el
indice con la base), tiene que ser la YEMA la que cae sobre las falanges medias
del indice y del medio. De ahi que entren apoyoIdx y apoyoMed en el coste.
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
OUT = ROOT / "tools" / "screenshots" / "search_s5"
OUT.mkdir(parents=True, exist_ok=True)
REF = ROOT / "tools" / "screenshots" / "final_s" / "_ref.png"

se9.URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=s13"

GAP_MIN = 0.125

OBJETIVO = {
    "sobreFrente": (0.18, 12.0),
    "apoyoIdx": (0.21, 6.0),
    "apoyoMed": (0.21, 6.0),
    "camU": (0.48, 6.0),
    "camAlt": (-0.10, 3.0),
    "gapDedos": (0.18, 8.0),
    "thLatDir": (0.75, 2.5),
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


def candidatas():
    for tc, z, y, x, t2x, t2y in itertools.product(
        (0.2, 0.4),
        (5, 20, 35),
        (-85, -70, -55),
        (0, 15, 30),
        (20, 40, 60),
        (0, -25),
    ):
        thumb = {T1: {"x": x, "y": y, "z": z}, T2: {"x": t2x, "y": t2y}}
        yield f"c{tc}_z{z}_y{y}_x{x}_t{t2x}_{t2y}", puno_s(tcurl=tc, thumb=thumb)


def linea(nombre, m):
    return (
        f"{nombre:28s} sobre={m['sobreFrente']:+6.3f} gap={m['gapDedos']:.3f} "
        f"apI={m['apoyoIdx']:.3f} apM={m['apoyoMed']:.3f} "
        f"camU={m['camU']:+5.2f} camAlt={m['camAlt']:+5.2f} "
        f"camCima={m['camCima']:+5.2f} lat={m['thLatDir']:+5.2f}"
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

    hoja(items, OUT / "_hoja.png", cols=4, cell=380, titulo="S · yema apoyada")
    (OUT / "_top.json").write_text(
        json.dumps([{k: r[k] for k in ("nombre", "coste", "m", "pose")}
                    for r in res[:20]], indent=2),
        "utf-8",
    )
    print("Capturas en", OUT)


if __name__ == "__main__":
    main()
