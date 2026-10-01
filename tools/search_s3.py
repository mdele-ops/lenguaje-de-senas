"""S lab 10: que el pulgar se APOYE en los dedos, no que quede por delante.

Las finalistas del lab 9 se leen bien de frente pero de perfil el pulgar sale
disparado hacia el espectador: camDelante rondaba 0.5 palmas, o sea medio puno
de separacion. El fallo estaba en el objetivo, que premiaba "cuanto mas
delante, mejor"; en la lamina el pulgar esta TUMBADO ENCIMA de las falanges
medias, tocandolas, y eso es una franja estrecha:

  camDelante  ~0.12  justo el grosor del pulgar por delante del frente del puno
  gapDedos    ~0.09  se apoya: ni flotando (>0.2) ni metido en la malla (<0.04)
  apoyoMed    ~0.14  el cuerpo del pulgar cae sobre la falange media del medio

Ademas entra en el barrido la flexion del propio pulgar (tcurl), que es lo que
lo hace envolver el puno en vez de quedarse tieso.
"""
import itertools
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from enfoque_r import MANO, captura, hoja
from pose_lab_e import T1, T2, T3, free_camera
from pose_lab_s import MEASURE_JS
from search_s2 import puno_s
from ver_s import VISTAS, cam
import search_e9 as se9
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "search_s3"
OUT.mkdir(parents=True, exist_ok=True)
REF = ROOT / "tools" / "screenshots" / "final_s" / "_ref.png"

se9.URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=s10"

OBJETIVO = {
    "camU": (0.48, 5.0),
    "camAlt": (-0.15, 3.0),
    "camDelante": (0.12, 8.0),
    "gapDedos": (0.090, 25.0),
    "apoyoMed": (0.140, 8.0),
    "thLatDir": (0.85, 2.0),
}


def puntua(m):
    if m.get("error") or "camU" not in m:
        return 9e9
    coste = sum(p * abs(m[k] - ideal) for k, (ideal, p) in OBJETIVO.items())
    if m["camDelante"] <= 0.04:
        coste += 50                            # se fue por detras del puno
    if m["camCima"] > -0.05:
        coste += 20 * (m["camCima"] + 0.05)    # asoma por encima de los dedos
    if m["gapDedos"] < 0.035:
        coste += 40                            # atraviesa la malla
    return coste


def candidatas():
    for tc, z, x, y, t2x in itertools.product(
        (0.0, 0.25, 0.5),
        (10, 20, 30, 40),
        (0, 12, 24),
        (-30, -15, 0, 15, 30),
        (10, 25, 40),
    ):
        yield (
            f"c{tc}_z{z}_x{x}_y{y}_t{t2x}",
            puno_s(tcurl=tc, thumb={T1: {"x": x, "y": y, "z": z}, T2: {"x": t2x}}),
        )


def linea(nombre, m):
    return (
        f"{nombre:24s} camU={m['camU']:+5.2f} camAlt={m['camAlt']:+5.2f} "
        f"camCima={m['camCima']:+5.2f} camDel={m['camDelante']:+6.3f} "
        f"gap={m['gapDedos']:.3f} apoyo={m['apoyoMed']:.3f} "
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
                items.append((f"{r['nombre'][:20]} {vista}", ruta))

        browser.close()

    hoja(items, OUT / "_hoja.png", cols=4, cell=380, titulo="S · pulgar apoyado")
    (OUT / "_top.json").write_text(
        json.dumps([{k: r[k] for k in ("nombre", "coste", "m", "pose")}
                    for r in res[:20]], indent=2),
        "utf-8",
    )
    print("Capturas en", OUT)


if __name__ == "__main__":
    main()
