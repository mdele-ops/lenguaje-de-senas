"""S lab 4: cerrar el puno de verdad antes de colocar el pulgar.

En los renders del lab 2 el puno de la A y de la S no acaba de cerrarse: los
dedos se quedan en garra, con las yemas separadas de la palma. Con la mano asi
no hay pulgar que arregle la letra, porque no existe el frente plano de
falanges medias sobre el que la S se apoya.

Se mide:
  puntaPalma  yema del indice -> muneca. En un puno cerrado la yema baja a la
              base de la palma, asi que este numero tiene que caer.
  freMax      cuanto sobresale el punto mas adelantado de los dedos. Es el
              frente del puno; si no crece, el puno no se esta cerrando.
  puntaFre    la yema por delante de su nudillo: en un puno vuelve hacia la
              palma, asi que baja cuando el dedo termina de plegarse.
"""
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from enfoque_r import MANO, captura, hoja
from pose_lab_e import BONES, free_camera
from pose_lab_s import MEASURE_JS, pose_s
from ver_s import VISTAS, cam
import search_e9 as se9
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "puno_s"
OUT.mkdir(parents=True, exist_ok=True)
REF = ROOT / "tools" / "screenshots" / "ref_S_big.png"

se9.URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=s4"


def flexion(prox=0, midd=0, dist=0):
    """Grados extra de flexion repartidos por falange en los cuatro dedos."""
    ex = {}
    for dedo in ("index", "middle", "ring", "pinky"):
        cad = BONES[dedo]
        if prox:
            ex[cad[0]] = {"x": prox}
        if midd:
            ex[cad[1]] = {"x": midd}
        if dist:
            ex[cad[2]] = {"x": dist}
    return ex


def linea(nombre, m):
    return (
        f"{nombre:16s} puntaPalma={m['puntaPalma']:.3f} freMax={m['freMax']:+.3f} "
        f"puntaFre={m['puntaFre']:+.3f} puntaAlt={m['puntaAlt']:+.3f} "
        f"pipFre={m['pipFre']:+.3f}"
    )


def main():
    casos = {}
    for c in (0.8, 0.95, 1.0):
        casos[f"curl{c}"] = pose_s(cierre=c, tcurl=0.0)
    # curl solo llega hasta cierto punto; el resto se pide por hueso
    for extra in (10, 20, 30, 40):
        casos[f"c1_mid{extra}"] = pose_s(
            cierre=1.0, tcurl=0.0, dedos=None
        )
        casos[f"c1_mid{extra}"]["extra"].update(flexion(midd=extra))
    for extra in (15, 30):
        casos[f"c1_prox{extra}"] = pose_s(cierre=1.0, tcurl=0.0)
        casos[f"c1_prox{extra}"]["extra"].update(flexion(prox=extra, midd=30))
    for extra in (15, 30):
        casos[f"c1_dist{extra}"] = pose_s(cierre=1.0, tcurl=0.0)
        casos[f"c1_dist{extra}"]["extra"].update(flexion(midd=30, dist=extra))

    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 1000, "height": 1000})
        time.sleep(0.4)
        free_camera(page)

        items = [("REF lamina", REF)] if REF.exists() else []
        medidas = {}
        for nombre, pose in casos.items():
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
            time.sleep(0.28)
            m = page.evaluate(MEASURE_JS)
            medidas[nombre] = m
            print(" ", linea(nombre, m))
            for vista, orbit in VISTAS[:2]:
                ruta = OUT / f"{nombre}_{vista}.png"
                cam(page, orbit)
                captura(page, ruta, MANO, margen=0.30)
                items.append((f"{nombre} {vista}", ruta))

        browser.close()

    hoja(items, OUT / "_hoja.png", cols=5, cell=300, titulo="S · cierre del puno")
    (OUT / "_medidas.json").write_text(json.dumps(medidas, indent=2), "utf-8")
    print("Capturas en", OUT)


if __name__ == "__main__":
    main()
