"""R lab 7: el pulgar, que es lo ultimo que queda fuera de sitio.

Con el cruce ya resuelto, de perfil la mano hace una escuadra: el pulgar sale
recto hacia el frente como en una L. En la lamina va TUMBADO sobre el anular y
el menique recogidos, tapandolos, con la yema hacia el centro de la palma.

Se barre el pulgar entero (curl, apertura y los giros de Thumb1/Thumb2) y se
puntua con:
  thumbSobre  yema del pulgar -> yema del anular. Pequeno = lo esta tapando.
  thLat       posicion de la yema en el eje de los nudillos. Negativo = el
              pulgar se sale por el lado del indice, que es la escuadra.
  thHoriz     1 = tumbado, 0 = de pie.
  thFuera     cuanto se despega de la palma hacia el espectador.
"""
import itertools
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from enfoque_r import MANO, captura, hoja
from eje_r import CAM_FOV, CAM_ORBIT, CAM_TARGET, cam
from pose_lab_e import T1, T2, free_camera
from pose_lab_r import MEASURE_JS
from search_r import banda, cruzar
import search_e9 as se9
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "pulgar_r"
OUT.mkdir(parents=True, exist_ok=True)
REF = ROOT / "tools" / "screenshots" / "lamina_R.png"

se9.URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=r7"

# el cruce ya elegido; aqui no se toca
CRUCE = dict(iz=22, mz=-26, ix=32, ix2=-40, iz2=-10)

BANDAS_TH = {
    "thumbSobre": (0.18, 0.55),
    "thLat": (0.20, 1.80),
    "thHoriz": (0.65, 1.00),
    "thFuera": (-1.00, -0.05),
}
PESOS_TH = {"thumbSobre": 4.0, "thLat": 3.0, "thHoriz": 2.5, "thFuera": 2.0}


def puntuar_th(m):
    return sum(
        PESOS_TH[k] * banda(m[k], *BANDAS_TH[k]) for k in BANDAS_TH
    )


def con_pulgar(tcurl, taside, t1y, t1z, t2x):
    thumb = {}
    if t1y or t1z:
        thumb[T1] = {k: v for k, v in (("y", t1y), ("z", t1z)) if v}
    if t2x:
        thumb[T2] = {"x": t2x}
    return cruzar(tcurl=tcurl, taside=taside, thumb=thumb, **CRUCE)


def linea(nombre, m, s):
    return (
        f"{nombre:34s} s={s:6.3f} sobre={m['thumbSobre']:.2f} "
        f"lat={m['thLat']:+5.2f} horiz={m['thHoriz']:.2f} "
        f"fuera={m['thFuera']:+5.2f} alto={m['thumbY']:+5.2f} "
        f"gap={m['gap']:.3f}"
    )


def main():
    rejilla = list(
        itertools.product(
            (0.35, 0.55, 0.75, 0.95),   # tcurl
            (-0.6, -0.2, 0.2),          # taside
            (-60, -30, 0, 30),          # t1y
            (0, 20, 40),                # t1z
            (0, 30, 60),                # t2x
        )
    )

    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 1000, "height": 1000})
        time.sleep(0.4)
        free_camera(page)

        def medir(pose):
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
            return page.evaluate(MEASURE_JS)

        print(f"Barrido de pulgar: {len(rejilla)} combinaciones")
        res = []
        for k in rejilla:
            mm = medir(con_pulgar(*k))
            res.append((puntuar_th(mm), k, mm))
        res.sort(key=lambda t: t[0])
        for s, k, mm in res[:20]:
            print(" ", linea(f"c{k[0]} a{k[1]} y{k[2]} z{k[3]} t2{k[4]}", mm, s))

        # se renderizan los mejores, pero separados entre si para no sacar
        # doce veces el mismo pulgar con medio grado de diferencia
        elegidos, vistos = [], set()
        for s, k, mm in res:
            firma = (round(mm["thumbSobre"], 1), round(mm["thLat"], 1),
                     round(mm["thHoriz"], 1))
            if firma in vistos:
                continue
            vistos.add(firma)
            elegidos.append((s, k, mm))
            if len(elegidos) >= 11:
                break

        items = [("REF lamina", REF)] if REF.exists() else []
        perfiles = list(items)
        detalle = {}
        for s, k, mm in elegidos:
            nombre = f"c{k[0]}_a{k[1]}_y{k[2]}_z{k[3]}_t{k[4]}"
            detalle[nombre] = dict(
                tcurl=k[0], taside=k[1], t1y=k[2], t1z=k[3], t2x=k[4], score=s
            )
            page.evaluate(
                "(x) => window.__LSM_CONTROLLER__.applyTestPose(x)",
                con_pulgar(*k),
            )
            time.sleep(0.3)
            cam(page, CAM_TARGET, CAM_ORBIT, CAM_FOV)
            r1 = OUT / f"{nombre}_frente.png"
            captura(page, r1, MANO, margen=0.28)
            items.append((nombre, r1))
            cam(page, CAM_TARGET, "-80deg 84deg 2.5m", CAM_FOV)
            r2 = OUT / f"{nombre}_perfil.png"
            captura(page, r2, MANO, margen=0.28)
            perfiles.append((nombre, r2))

        browser.close()

    hoja(items, OUT / "_frente.png", cols=4, cell=330, titulo="R · pulgar de frente")
    hoja(perfiles, OUT / "_perfil.png", cols=4, cell=330, titulo="R · pulgar de perfil")
    (OUT / "_casos.json").write_text(json.dumps(detalle, indent=2), "utf-8")


if __name__ == "__main__":
    main()
