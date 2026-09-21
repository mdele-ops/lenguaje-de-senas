"""S lab 8: afinar el pulgar sobre el puno ya cerrado.

El barrido grueso (lab 6) dejo claro que el pulgar cruza por delante con el eje
z del nudillo, pero salia demasiado de pie (thUpDir ~0.5) y con la yema
asomando por encima de los dedos. Aqui se busca fino sobre el puno del lab 7
(cierre 0.9 + 30 grados de nudillo) y se aprieta el objetivo:

  - el pulgar mas tumbado, como en la lamina, donde cruza en diagonal suave
  - la yema por debajo de lo alto del puno (camCima < 0): en la S el pulgar
    pasa POR DELANTE de los dedos, no asoma entre ellos
  - la yema parada en el medio/anular, sin llegar al canto del menique
"""
import itertools
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from enfoque_r import MANO, captura, hoja
from pose_lab_e import T1, T2, T3, free_camera
from pose_lab_s import MEASURE_JS, pose_s
from puno_s import flexion
from ver_s import VISTAS, cam
import search_e9 as se9
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "search_s2"
OUT.mkdir(parents=True, exist_ok=True)
REF = ROOT / "tools" / "screenshots" / "ref_S_big.png"

se9.URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=s8"

PUNO = dict(cierre=0.9, prox=30)

OBJETIVO = {
    "camU": (0.48, 5.0),
    "camAlt": (-0.15, 3.0),
    "camDelante": (0.32, 2.0),
    "thUpDir": (0.20, 3.0),
    "thLatDir": (0.85, 2.0),
}
GAP_MIN = 0.035


def puno_s(**kw):
    pose = pose_s(cierre=PUNO["cierre"], **kw)
    pose["extra"].update(flexion(prox=PUNO["prox"]))
    return pose


def puntua(m):
    if m.get("error") or "camU" not in m:
        return 9e9
    coste = sum(p * abs(m[k] - ideal) for k, (ideal, p) in OBJETIVO.items())
    if m["camDelante"] <= 0.05:
        coste += 50                      # se fue por detras del puno
    if m["camCima"] > -0.05:
        coste += 20 * (m["camCima"] + 0.05)   # asoma por encima de los dedos
    if m["gapDedos"] < GAP_MIN:
        coste += 30 * (GAP_MIN - m["gapDedos"]) / GAP_MIN
    return coste


def candidatas():
    for z, x, y, t2x, t3x in itertools.product(
        (20, 30, 40, 50),
        (0, 12, 24, 36),
        (-30, -15, 0, 15),
        (20, 35, 50),
        (0, 25),
    ):
        thumb = {T1: {"x": x, "y": y, "z": z}, T2: {"x": t2x}}
        if t3x:
            thumb[T3] = {"x": t3x}
        yield f"z{z}_x{x}_y{y}_t2{t2x}_t3{t3x}", puno_s(tcurl=0.0, thumb=thumb)


def linea(nombre, m):
    return (
        f"{nombre:26s} camU={m['camU']:+5.2f} camAlt={m['camAlt']:+5.2f} "
        f"camCima={m['camCima']:+5.2f} camDel={m['camDelante']:+6.3f} "
        f"lat={m['thLatDir']:+5.2f} up={m['thUpDir']:+5.2f} gap={m['gapDedos']:.3f}"
    )


def main():
    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 1000, "height": 1000})
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
        for r in res[:8]:
            page.evaluate(
                "(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", r["pose"]
            )
            time.sleep(0.3)
            for vista, orbit in VISTAS:
                ruta = OUT / f"{r['nombre']}_{vista}.png"
                cam(page, orbit)
                captura(page, ruta, MANO, margen=0.30)
                items.append((f"{r['nombre'][:20]} {vista}", ruta))

        browser.close()

    hoja(items, OUT / "_hoja.png", cols=3, cell=300, titulo="S · pulgar fino")
    (OUT / "_top.json").write_text(
        json.dumps([{k: r[k] for k in ("nombre", "coste", "m", "pose")}
                    for r in res[:20]], indent=2),
        "utf-8",
    )
    print("Capturas en", OUT)


if __name__ == "__main__":
    main()
