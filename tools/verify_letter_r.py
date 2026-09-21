"""Verifica la letra R tal y como sale en practica.html.

No mide la pose que uno le pasa a mano, sino la que el controlador acaba
poniendo en el esqueleto al pedir `mostrarSena('R')`: asi entra tambien la
transicion y cualquier cosa que el catalogo tenga mal escrita.

Lo que distingue una R de una U o una V son tres cosas, y las tres se
comprueban aqui:

  1. que los dedos esten CRUZADOS de verdad (cruce > 0: la yema del indice
     acaba del lado del medio y al reves), y que el cruce caiga a la altura de
     la falange media, como en la lamina.
  2. que no se ATRAVIESEN. Es el fallo que tenia la version anterior: los dos
     dedos ocupaban el mismo sitio (gap 0.05) y la malla se cortaba sola.
  3. que el indice pase por DELANTE (frenteMed > 0) y que los dos dedos vayan
     paralelos, sin abrirse en V vistos de perfil (abanico ~ 0).
"""
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from enfoque_r import MANO, captura, hoja
from eje_r import CAM_FOV, CAM_ORBIT, CAM_TARGET, cam
from pose_lab_e import free_camera
from pose_lab_r import MEASURE_JS
import search_e9 as se9
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "verify_r"
OUT.mkdir(parents=True, exist_ok=True)
REF = ROOT / "tools" / "screenshots" / "lamina_R.png"

se9.URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=vr"

CRITERIOS = {
    "cruce": (0.70, 1.30),        # yemas cambiadas de lado
    "crucePip": (-0.45, 0.10),    # el cruce cae en la falange media
    "gap": (0.150, 0.300),        # se rozan pero no se atraviesan
    "frenteMed": (0.08, 0.34),    # el indice monta por delante
    "abanico": (-0.12, 0.12),     # paralelos, no en V de perfil
    "sepYemas": (0.16, 0.42),     # las dos yemas juntas arriba
    "altIdx": (0.70, 1.10),       # indice estirado
    "altMed": (0.70, 1.10),       # medio estirado
    "vertIdx": (0.86, 1.00),      # y los dos apuntando arriba
    "vertMed": (0.84, 1.00),
    "punoMax": (0.00, 0.90),      # anular y menique recogidos
    "thumbSobre": (0.15, 0.60),   # pulgar apoyado sobre ellos
    "thHoriz": (0.60, 1.00),      # y tumbado, no en escuadra
}

VISTAS = (("frente", 0), ("tres_cuartos", -40), ("perfil", -80))


def rango(nombre, valor, lo, hi):
    bien = lo <= valor <= hi
    print(f"  {nombre:11s} {valor:+8.3f}  [{lo}, {hi}]  {'ok' if bien else 'FALLA'}")
    return bien


def main():
    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 1000, "height": 1000})
        time.sleep(0.3)
        free_camera(page)

        page.evaluate("() => window.__LSM_CONTROLLER__.mostrarSena('R')")
        time.sleep(2.6)  # la transicion del catalogo dura 2 s

        m = page.evaluate(MEASURE_JS)
        print("forma de la R:")
        ok = all(rango(k, m[k], *v) for k, v in CRITERIOS.items())
        print("\n  " + ("TODO OK" if ok else "REVISAR"))
        print("  rotulo:", page.inner_text("#anim-info").strip()[:120])

        items = [("REF lamina", REF)] if REF.exists() else []
        for vista, grados in VISTAS:
            cam(page, CAM_TARGET, f"{grados}deg 84deg 2.5m", CAM_FOV)
            ruta = OUT / f"R_{vista}.png"
            captura(page, ruta, MANO, margen=0.28)
            items.append((vista, ruta))

        # la vista de produccion entera, que es lo que ve el usuario
        cam(page, CAM_TARGET, CAM_ORBIT, CAM_FOV)
        page.query_selector("#viewer").screenshot(path=str(OUT / "R_produccion.png"))

        browser.close()

    hoja(items, OUT / "_verify.png", cols=4, cell=340, titulo="R · verificacion")
    (OUT / "_medidas.json").write_text(json.dumps(m, indent=2), "utf-8")
    print("Capturas en", OUT)


if __name__ == "__main__":
    main()
