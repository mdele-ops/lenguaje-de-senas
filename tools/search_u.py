"""U: busca indice y medio juntos y paralelos, sin cruzarse.

Parte de la geometria del lab 2:
  z6 junta (yemas=0.18, gap=0.16) sin cruzar (cruce=-0.63)
  z8 ya recorta malla (gap=0.11)
  el pulgar de la R (T1 y=-30 z=40, T2 x=60) queda sobre anular/menique

Si solo se gira el nudillo, los dos dedos se encuentran en A. El mismo truco
que la R en x (nudillo + falange media en sentido contrario) pero en z deja
los dos palos paralelos y pegados, que es lo que pide la foto.
"""
import itertools
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from eje_r import encuadrar
from enfoque_r import MANO, captura, hoja
from pose_lab_e import free_camera
from pose_lab_r import MEASURE_JS
from pose_lab_u import linea, pose_u
from search_e9 import abrir
import search_e9 as se9

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "search_u"
OUT.mkdir(parents=True, exist_ok=True)
REF = ROOT / "tools" / "screenshots" / "lab_u2" / "_ref.png"

se9.URL = "http://127.0.0.1:8006/practica.html?letra=%E2%97%8B&v=usearch"

BANDAS = {
    "gap": (0.145, 0.200),
    "sepYemas": (0.145, 0.230),
    "cruce": (-0.75, -0.15),
    "altIdx": (0.80, 1.05),
    "altMed": (0.80, 1.05),
    "punoMax": (0.50, 0.85),
    "thLat": (1.00, 2.20),
}
PESOS = {
    "gap": 8.0,
    "sepYemas": 5.0,
    "cruce": 4.0,
    "altIdx": 2.0,
    "altMed": 2.0,
    "punoMax": 1.5,
    "thLat": 2.0,
}


def banda(v, lo, hi):
    if v < lo:
        return (lo - v) / max(0.05, hi - lo)
    if v > hi:
        return (v - hi) / max(0.05, hi - lo)
    return 0.0


def puntuar(m):
    if m.get("error"):
        return 9e9
    coste = sum(PESOS[k] * banda(m[k], *BANDAS[k]) for k in BANDAS)
    # paralelos: el cruce en falange media y en yema debe ser el mismo
    coste += 6.0 * abs(m["cruce"] - m["crucePip"])
    if m["cruce"] > 0:
        coste += 20  # se cruzaron: eso es R, no U
    if m["gap"] < 0.10:
        coste += 12
    return coste


def candidatas():
    for iz, mz, iz2, mz2 in itertools.product(
        (5, 7, 9),
        (-5, -7, -9),
        (0, -5, -9),
        (0, 5, 9),
    ):
        yield (
            f"iz{iz}_mz{mz}_i2{iz2}_m2{mz2}",
            pose_u(iz=iz, mz=mz, iz2=iz2, mz2=mz2, arm_z=-18),
        )


def main():
    catalogo = json.loads((ROOT / "data" / "catalogo-lsm.json").read_text("utf-8"))
    vieja = next(s for s in catalogo["senas"] if s["letra"] == "U")["pose"]

    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 900, "height": 900})
        time.sleep(0.3)
        free_camera(page)

        m0 = page.evaluate(
            "(x) => { window.__LSM_CONTROLLER__.applyTestPose(x); }", vieja
        )
        time.sleep(0.25)
        m0 = page.evaluate(MEASURE_JS)
        print("CATALOGO", linea("U_vieja", m0), "s=", round(puntuar(m0), 3))

        ranking = []
        for nombre, pose in candidatas():
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
            m = page.evaluate(MEASURE_JS)
            s = puntuar(m)
            ranking.append((s, nombre, pose, m))
        ranking.sort(key=lambda t: t[0])

        print("TOP 10")
        for s, nombre, pose, m in ranking[:10]:
            print(f"  s={s:6.3f}  {linea(nombre, m)}  dCruce={abs(m['cruce']-m['crucePip']):.3f}")

        (OUT / "_top.json").write_text(
            json.dumps(
                [
                    {"score": s, "nombre": n, "pose": p, "metricas": m}
                    for s, n, p, m in ranking[:12]
                ],
                indent=2,
            ),
            encoding="utf-8",
        )

        items = [("REF foto", REF)] if REF.exists() else []
        items.append(("catalogo", None))
        page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", vieja)
        time.sleep(0.28)
        encuadrar(page, 0)
        ruta = OUT / "catalogo.png"
        captura(page, ruta, MANO, margen=0.22, lado=520)
        items[-1] = ("catalogo", ruta)

        for s, nombre, pose, m in ranking[:6]:
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
            time.sleep(0.28)
            encuadrar(page, 0)
            ruta = OUT / f"{nombre}.png"
            captura(page, ruta, MANO, margen=0.22, lado=520)
            items.append((f"{s:.2f} {nombre}", ruta))

        browser.close()

    hoja(items, OUT / "_hoja.png", cols=4, cell=360, titulo="U · busqueda")
    print("Capturas en", OUT)


if __name__ == "__main__":
    main()
