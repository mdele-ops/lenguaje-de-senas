"""Verifica la letra S tal y como sale en practica.html.

No mide la pose que uno le pasa a mano, sino la que el controlador acaba
poniendo en el esqueleto al pedir `mostrarSena('S')`: asi entra tambien la
transicion y cualquier cosa que el catalogo tenga mal escrita.

Lo que separa una S de una A (las dos son un puno) es donde va el pulgar, y es
justo lo que fallaba antes: la S del catalogo tenia el pulgar descolgado por la
palma, medio palmo por debajo de los dedos. Aqui se comprueban las cuatro cosas
que la hacen legible:

  1. que el puno este CERRADO (punoMax bajo, yemas recogidas).
  2. que el pulgar CRUCE por delante: camU dice hasta donde llega la yema entre
     el nudillo del indice (0) y el del menique (1); en la A se queda en ~0.
  3. que se APOYE y no flote ni atraviese la malla: sobreFrente mide lo que
     sobresale la yema del frente del puno y gapDedos la separacion real entre
     las cadenas de huesos. Los huesos van por el centro de la carne, asi que
     por debajo de ~0.13 el pulgar ya se mete dentro del dedo.
  4. que vaya TUMBADO y a la altura de las falanges medias, sin asomar por
     encima del puno (camCima < 0).
"""
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from enfoque_r import MANO, captura, hoja
from eje_r import CAM_FOV, CAM_ORBIT, CAM_TARGET, cam
from pose_lab_e import free_camera
from pose_lab_s import MEASURE_JS
import search_e9 as se9
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "verify_s"
OUT.mkdir(parents=True, exist_ok=True)
REF = ROOT / "tools" / "screenshots" / "final_s" / "_ref.png"

se9.URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=vs"

CRITERIOS = {
    "punoMax": (0.00, 0.72),       # los cuatro dedos recogidos
    "camU": (0.45, 0.95),          # la yema cruza hasta el medio/anular
    "camAlt": (-0.70, 0.10),       # a la altura de las falanges medias
    "camCima": (-1.20, -0.03),     # sin asomar por encima del puno
    "sobreFrente": (0.08, 0.28),   # apoyada en el frente, ni dentro ni flotando
    "gapDedos": (0.130, 0.320),    # roza los dedos pero no los atraviesa
    "apoyoMed": (0.15, 0.32),      # el cuerpo del pulgar sobre el medio
    "thLatDir": (0.55, 1.00),      # tumbado cruzando, no de pie como en la A
    "thUpDir": (-0.20, 0.60),
}

VISTAS = (("frente", 0), ("tres_cuartos", -40), ("perfil", -80))


def rango(nombre, valor, lo, hi):
    bien = lo <= valor <= hi
    print(f"  {nombre:12s} {valor:+8.3f}  [{lo}, {hi}]  {'ok' if bien else 'FALLA'}")
    return bien


def main():
    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 1000, "height": 1000})
        time.sleep(0.3)
        free_camera(page)
        cam(page, CAM_TARGET, CAM_ORBIT, CAM_FOV)

        page.evaluate("() => window.__LSM_CONTROLLER__.mostrarSena('S')")
        time.sleep(2.6)  # la transicion del catalogo dura 2 s

        m = page.evaluate(MEASURE_JS)
        print("forma de la S:")
        ok = all(rango(k, m[k], *v) for k, v in CRITERIOS.items())
        print("\n  " + ("TODO OK" if ok else "REVISAR"))
        print("  rotulo:", page.inner_text("#anim-info").strip()[:120])

        items = [("REF lamina", REF)] if REF.exists() else []
        for vista, grados in VISTAS:
            cam(page, CAM_TARGET, f"{grados}deg 84deg 2.5m", CAM_FOV)
            ruta = OUT / f"S_{vista}.png"
            captura(page, ruta, MANO, margen=0.26, lado=460)
            items.append((vista, ruta))

        # la vista de produccion entera, que es lo que ve el usuario
        cam(page, CAM_TARGET, CAM_ORBIT, CAM_FOV)
        page.query_selector("#viewer").screenshot(path=str(OUT / "S_produccion.png"))

        browser.close()

    hoja(items, OUT / "_verify.png", cols=4, cell=380, titulo="S · verificacion")
    (OUT / "_medidas.json").write_text(json.dumps(m, indent=2), "utf-8")
    print("Capturas en", OUT)


if __name__ == "__main__":
    main()
