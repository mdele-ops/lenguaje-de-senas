"""R lab 4: mira las candidatas al lado de la lamina, todas al mismo tamano.

La geometria ya dice que los dedos se cruzan y no se atraviesan; lo que no dice
es si la letra SE LEE. Esto renderiza cada candidata desde el frente (como la
ve el usuario), de tres cuartos y de perfil, recortando siempre sobre la mano
con `enfoque_r`, y arma hojas de contactos con la lamina en la primera casilla.

Uso:
  py tools/ver_r.py                      las candidatas escritas aqui
  py tools/ver_r.py screenshots/search_r.json   el top de la busqueda
"""
import json
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from enfoque_r import DEDOS, MANO, captura, hoja
from eje_r import CAM_FOV, CAM_ORBIT, CAM_TARGET, cam
from pose_lab_e import free_camera
from pose_lab_r import MEASURE_JS
from search_r import cruzar, puntuar
import search_e9 as se9
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "ver_r"
OUT.mkdir(parents=True, exist_ok=True)
# la lamina oficial del propio proyecto se ve mucho mejor que el recorte que
# mando el usuario, y es la misma seña
REF_MANO = ROOT / "tools" / "screenshots" / "lamina_R.png"
REF_DEDOS = ROOT / "tools" / "screenshots" / "lamina_R_cruce.png"

se9.URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=r4"

CANDIDATAS = {
    # las mejores de search_r: el INDICE monta por delante (ix positivo en el
    # nudillo, negativo en la falange media para volver a enderezarlo) y iz2
    # vuelve a juntar las yemas por encima del cruce
    "a_ix32_z2": dict(iz=22, mz=-26, ix=32, ix2=-40, iz2=-10),
    "b_ix26_z2": dict(iz=22, mz=-26, ix=26, ix2=-30, iz2=-10),
    "c_ix32_z2_ty": dict(iz=22, mz=-26, ix=32, ix2=-40, iz2=-10, ity=8),
    "d_iz26_mz22": dict(iz=26, mz=-22, ix=26, ix2=-30, iz2=-10, mty=8),
    "e_ix38_sinz2": dict(iz=18, mz=-26, ix=38, ix2=-40),
    "f_ix32_z2_20": dict(iz=22, mz=-26, ix=32, ix2=-40, iz2=-20),
    "g_ix32_mz2": dict(iz=22, mz=-26, ix=32, ix2=-40, iz2=-10, mz2=10),
    "h_iz26_mz26": dict(iz=26, mz=-26, ix=38, ix2=-40, iz2=-10, mz2=10),
}

VISTAS = (("frente", 0), ("tres_cuartos", -35), ("perfil", -80))


def main():
    casos = dict(CANDIDATAS)
    if len(sys.argv) > 1:
        datos = json.loads(Path(sys.argv[1]).read_text("utf-8"))
        casos = {}
        vistos = set()
        for i, item in enumerate(datos):
            kw = item["kw"]
            clave = tuple(sorted(kw.items()))
            if clave in vistos:
                continue
            vistos.add(clave)
            casos[f"{i:02d}"] = kw
            if len(casos) >= 12:
                break

    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 1000, "height": 1000})
        time.sleep(0.4)
        free_camera(page)

        hojas = {v: [] for v, _ in VISTAS}
        hojas["dedos"] = []
        if REF_MANO.exists():
            for v, _ in VISTAS:
                hojas[v].append(("REF lamina", REF_MANO))
            hojas["dedos"].append(("REF lamina", REF_DEDOS))

        poses = {}
        for nombre, kw in casos.items():
            pose = cruzar(**kw)
            poses[nombre] = {"kw": kw, "pose": pose}
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
            time.sleep(0.3)
            m = page.evaluate(MEASURE_JS)
            print(
                f"  {nombre:16s} s={puntuar(m):6.3f} "
                f"cruce={m['cruce']:+5.2f}/{m['crucePip']:+5.2f} "
                f"gap={m['gap']:.3f} frente={m['frenteMed']:+5.2f} "
                f"aban={m['abanico']:+5.2f} yemas={m['sepYemas']:.2f}"
            )

            for vista, grados in VISTAS:
                cam(page, CAM_TARGET, f"{grados}deg 84deg 2.5m", CAM_FOV)
                ruta = OUT / f"{nombre}_{vista}.png"
                captura(page, ruta, MANO, margen=0.30)
                hojas[vista].append((nombre, ruta))

            cam(page, CAM_TARGET, CAM_ORBIT, CAM_FOV)
            ruta = OUT / f"{nombre}_dedos.png"
            captura(page, ruta, DEDOS, margen=0.55)
            hojas["dedos"].append((nombre, ruta))

        browser.close()

    for vista, items in hojas.items():
        hoja(items, OUT / f"_{vista}.png", cols=4, cell=340, titulo=f"R · {vista}")
    (OUT / "_casos.json").write_text(json.dumps(poses, indent=2), "utf-8")


if __name__ == "__main__":
    main()
