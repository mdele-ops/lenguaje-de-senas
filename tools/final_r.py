"""R: comparativa final y escritura en el catalogo.

  py tools/final_r.py            solo compara (lamina, R vieja y finalistas)
  py tools/final_r.py --guardar  ademas escribe la R elegida en el catalogo

La pose elegida sale de los labs anteriores:
  cruce    indice +22 en z y medio -26: las yemas se cambian de lado y la
           silueta hace la equis que distingue la R de la U.
  delante  el indice se adelanta 32 en el nudillo y se vuelve a enderezar -40
           en la falange media, asi monta por delante del medio (como en la
           lamina) sin abrirse en V vista de perfil.
  yemas    -10 en z en la falange media del indice para que las dos yemas
           vuelvan a juntarse por encima del cruce.
  pulgar   tumbado sobre el anular y el menique recogidos, no en escuadra.
"""
import json
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from enfoque_r import MANO, captura, hoja
from eje_r import CAM_FOV, CAM_ORBIT, CAM_TARGET, cam
from pose_lab_e import T1, T2, free_camera
from pose_lab_r import MEASURE_JS
from search_r import cruzar, puntuar
import search_e9 as se9
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "final_r"
OUT.mkdir(parents=True, exist_ok=True)
REF = ROOT / "tools" / "screenshots" / "lamina_R.png"
CATALOGO = ROOT / "data" / "catalogo-lsm.json"

se9.URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=rf"

CRUCE = dict(iz=22, mz=-26, ix=32, ix2=-40, iz2=-10)


def pulgar(t1y, t1z, t2x, tcurl=0.35, taside=-0.6):
    thumb = {T1: {k: v for k, v in (("y", t1y), ("z", t1z)) if v}}
    if t2x:
        thumb[T2] = {"x": t2x}
    return dict(tcurl=tcurl, taside=taside, thumb=thumb)


FINALISTAS = {
    "t0_pulgar_simple": dict(CRUCE, tcurl=0.55, taside=0.0),
    "t1_y60_z20": dict(CRUCE, **pulgar(-60, 20, 60)),
    "t2_y60_z40": dict(CRUCE, **pulgar(-60, 40, 60)),
    "t3_y30_z40": dict(CRUCE, **pulgar(-30, 40, 60)),
    "t4_y30_z20": dict(CRUCE, **pulgar(-30, 20, 60)),
}

ELEGIDA = "t3_y30_z40"

VISTAS = (("frente", 0), ("tres_cuartos", -40), ("perfil", -80))

DESCRIPCION = (
    "Índice y medio estirados hacia arriba y cruzados: el índice se adelanta "
    "y monta por delante del medio, de modo que las dos yemas quedan "
    "cambiadas de lado y juntas arriba, dibujando la equis de la R. Anular y "
    "meñique se recogen en el puño con el pulgar tumbado encima."
)


def guardar(pose):
    datos = json.loads(CATALOGO.read_text("utf-8"))
    sena = next(s for s in datos["senas"] if s["letra"] == "R")
    sena["pose"] = pose
    sena["descripcion"] = DESCRIPCION
    partes = datos["version"].split(".")
    partes[-1] = str(int(partes[-1]) + 1)
    datos["version"] = ".".join(partes)
    CATALOGO.write_text(
        json.dumps(datos, ensure_ascii=False, indent=2) + "\n", "utf-8"
    )
    print(f"Catalogo actualizado (version {datos['version']})")


def main():
    catalogo = json.loads(CATALOGO.read_text("utf-8"))
    vieja = next(s for s in catalogo["senas"] if s["letra"] == "R")["pose"]

    casos = {"00_R_vieja": vieja}
    for nombre, kw in FINALISTAS.items():
        casos[nombre] = cruzar(**kw)

    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 1000, "height": 1000})
        time.sleep(0.4)
        free_camera(page)

        hojas = {v: ([("REF lamina", REF)] if REF.exists() else []) for v, _ in VISTAS}
        for nombre, pose in casos.items():
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
            time.sleep(0.3)
            m = page.evaluate(MEASURE_JS)
            print(
                f"  {nombre:18s} s={puntuar(m):6.3f} cruce={m['cruce']:+5.2f} "
                f"gap={m['gap']:.3f} frente={m['frenteMed']:+5.2f} "
                f"yemas={m['sepYemas']:.2f} pulgar={m['thumbSobre']:.2f}/"
                f"{m['thHoriz']:.2f}"
            )
            for vista, grados in VISTAS:
                cam(page, CAM_TARGET, f"{grados}deg 84deg 2.5m", CAM_FOV)
                ruta = OUT / f"{nombre}_{vista}.png"
                captura(page, ruta, MANO, margen=0.28)
                hojas[vista].append((nombre, ruta))

        browser.close()

    for vista, items in hojas.items():
        hoja(items, OUT / f"_{vista}.png", cols=3, cell=360, titulo=f"R · {vista}")

    if "--guardar" in sys.argv:
        guardar(casos[ELEGIDA])


if __name__ == "__main__":
    main()
