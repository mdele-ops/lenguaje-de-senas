"""S lab 12: la busqueda buena, ya con los ejes que hacen falta.

El lab 11 separa por fin los dos movimientos que la S necesita y que hasta
ahora estaba mezclando:

  T1.z (+)  cruza el pulgar del indice hacia el menique
  T1.y (-)  lo mete contra el puno; es el que faltaba, y por eso ninguna
            busqueda anterior conseguia bajar sobreFrente de 0.35

Con los dos a la vez el pulgar cruza Y se apoya. Lo que se le pide:

  sobreFrente ~0.16  la yema apenas por delante del frente del puno: apoyada
  gapDedos    >=0.14 los huesos van por el centro de la carne, asi que por
                     debajo de eso la malla del pulgar entra en la del dedo
  camU        ~0.48  la yema para en el medio/anular, no en el canto
  camAlt      ~-0.10 cruza a la altura de las falanges medias
  camCima     <0     y no asoma por encima del puno
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
OUT = ROOT / "tools" / "screenshots" / "search_s4"
OUT.mkdir(parents=True, exist_ok=True)
REF = ROOT / "tools" / "screenshots" / "final_s" / "_ref.png"

se9.URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=s12"

GAP_MIN = 0.140

OBJETIVO = {
    "sobreFrente": (0.16, 12.0),
    "camU": (0.48, 6.0),
    "camAlt": (-0.10, 3.0),
    "gapDedos": (0.19, 10.0),
    "thLatDir": (0.75, 2.5),
}


def puntua(m):
    if m.get("error") or "camU" not in m:
        return 9e9
    coste = sum(p * abs(m[k] - ideal) for k, (ideal, p) in OBJETIVO.items())
    if m["gapDedos"] < GAP_MIN:
        coste += 60 * (GAP_MIN - m["gapDedos"]) / GAP_MIN
    if m["sobreFrente"] < 0.04:
        coste += 40          # el pulgar se ha hundido dentro del puno
    if m["camCima"] > -0.04:
        coste += 25 * (m["camCima"] + 0.04)
    return coste


def candidatas():
    for tc, z, y, x, t2x in itertools.product(
        (0.25, 0.45),
        (15, 30, 45, 60),
        (-45, -35, -25, -15),
        (-10, 5, 20, 35),
        (10, 30, 50),
    ):
        yield (
            f"c{tc}_z{z}_y{y}_x{x}_t{t2x}",
            puno_s(tcurl=tc, thumb={T1: {"x": x, "y": y, "z": z}, T2: {"x": t2x}}),
        )


def linea(nombre, m):
    return (
        f"{nombre:26s} sobre={m['sobreFrente']:+6.3f} gap={m['gapDedos']:.3f} "
        f"camU={m['camU']:+5.2f} camAlt={m['camAlt']:+5.2f} "
        f"camCima={m['camCima']:+5.2f} lat={m['thLatDir']:+5.2f} "
        f"up={m['thUpDir']:+5.2f}"
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
                items.append((f"{r['nombre'][:20]} {vista}", ruta))

        browser.close()

    hoja(items, OUT / "_hoja.png", cols=4, cell=380, titulo="S · cruza y apoya")
    (OUT / "_top.json").write_text(
        json.dumps([{k: r[k] for k in ("nombre", "coste", "m", "pose")}
                    for r in res[:20]], indent=2),
        "utf-8",
    )
    print("Capturas en", OUT)


if __name__ == "__main__":
    main()
