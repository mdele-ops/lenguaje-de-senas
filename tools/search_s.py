"""S lab 6: barrido del pulgar sobre el puno cerrado.

Del lab 1 salen los ejes utiles del nudillo del pulgar: `z` es el que lo cruza
hacia el menique, `x` el que lo sube o lo baja y `y` el que lo separa de la
palma. Aqui se recorren esos tres mas la flexion de la falange (T2.x) y se
puntua cada combinacion contra lo que pide la lamina.

Lo que se le exige a la pose, todo medido con la camara de produccion para que
sea lo que el usuario ve y no un artefacto del signo de la normal:

  camDelante > 0   el pulgar pasa por DELANTE de los dedos, no por detras
  camU ~ 0.5       la yema cruza hasta el medio/anular (0 = indice, 1 = menique)
  camAlt ~ 0       cruza a la altura de las falanges medias, no por la palma
  thLatDir alto    va tumbado cruzando, no de pie como en la A
  gapDedos > 0     roza los dedos pero no los atraviesa
"""
import itertools
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from enfoque_r import MANO, captura, hoja
from pose_lab_e import T1, T2, T3, free_camera
from pose_lab_s import MEASURE_JS, pose_s
from ver_s import VISTAS, cam
import search_e9 as se9
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "search_s"
OUT.mkdir(parents=True, exist_ok=True)
REF = ROOT / "tools" / "screenshots" / "ref_S_big.png"

se9.URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=s6"

# valor ideal y cuanto pesa cada cosa
OBJETIVO = {
    "camDelante": (0.30, 3.0),
    "camU": (0.50, 4.0),
    "camAlt": (0.00, 2.5),
    "thLatDir": (0.80, 2.0),
    "thUpDir": (0.00, 1.0),
}
GAP_MIN = 0.035


def puntua(m):
    """Menos es mejor. Atravesar los dedos descalifica."""
    if m.get("error") or "camU" not in m:
        return 9e9
    coste = sum(
        peso * abs(m[k] - ideal) for k, (ideal, peso) in OBJETIVO.items()
    )
    if m["camDelante"] <= 0.05:
        coste += 50          # el pulgar se ha ido por detras del puno
    if m["gapDedos"] < GAP_MIN:
        coste += 30 * (GAP_MIN - m["gapDedos"]) / GAP_MIN
    return coste


def candidatas():
    for z, x, y, t2x in itertools.product(
        (30, 45, 60, 75),
        (-15, 0, 15, 30),
        (-40, -20, 0, 20),
        (0, 20, 40, 60),
    ):
        yield (
            f"z{z}_x{x}_y{y}_t{t2x}",
            pose_s(
                cierre=1.0,
                tcurl=0.0,
                thumb={T1: {"x": x, "y": y, "z": z}, T2: {"x": t2x}},
            ),
        )


def linea(nombre, m):
    return (
        f"{nombre:24s} camU={m['camU']:+6.2f} camDel={m['camDelante']:+6.3f} "
        f"camAlt={m['camAlt']:+6.2f} lat={m['thLatDir']:+5.2f} "
        f"up={m['thUpDir']:+5.2f} gap={m['gapDedos']:.3f}"
    )


def main():
    catalogo = json.loads((ROOT / "data" / "catalogo-lsm.json").read_text("utf-8"))
    por_letra = {s["letra"]: s for s in catalogo["senas"]}

    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 1000, "height": 1000})
        time.sleep(0.4)
        free_camera(page)
        cam(page, "0deg 84deg 2.5m")   # medir siempre con la de produccion

        # Referencias: la B cruza el pulgar por delante de la palma, asi que
        # sirve para comprobar que camDelante sale positivo cuando toca.
        print("referencias:")
        for letra in ("B", "A", "S"):
            page.evaluate(
                "(x) => window.__LSM_CONTROLLER__.applyTestPose(x)",
                por_letra[letra]["pose"],
            )
            time.sleep(0.3)
            print("  ", linea(letra, page.evaluate(MEASURE_JS)))

        print("\nbarrido:")
        res = []
        for nombre, pose in candidatas():
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
            time.sleep(0.13)
            m = page.evaluate(MEASURE_JS)
            res.append({"nombre": nombre, "coste": puntua(m), "m": m, "pose": pose})

        res.sort(key=lambda r: r["coste"])
        for r in res[:12]:
            print(f"  {r['coste']:7.3f}  {linea(r['nombre'], r['m'])}")

        items = [("REF lamina", REF)] if REF.exists() else []
        for r in res[:8]:
            page.evaluate(
                "(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", r["pose"]
            )
            time.sleep(0.3)
            for vista, orbit in VISTAS:
                ruta = OUT / f"{r['nombre']}_{vista}.png"
                cam(page, orbit)
                captura(page, ruta, MANO, margen=0.30)
                items.append((f"{r['nombre'][:18]} {vista}", ruta))

        browser.close()

    hoja(items, OUT / "_hoja.png", cols=3, cell=300, titulo="S · barrido pulgar")
    (OUT / "_top.json").write_text(
        json.dumps([{k: r[k] for k in ("nombre", "coste", "m", "pose")}
                    for r in res[:20]], indent=2),
        "utf-8",
    )
    print("Capturas en", OUT)


if __name__ == "__main__":
    main()
