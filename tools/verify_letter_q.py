"""Verifica la letra Q tal y como sale en practica.html: forma y movimiento.

La Q tiene dos cosas que comprobar y la segunda no se ve en una foto fija:

  1. la forma: pico indice-pulgar abierto y apuntando al suelo, con el resto
     de los dedos cerrados. Se contrasta con los angulos leidos en la lamina.
  2. el trazo: mientras corre el ciclo, el pico tiene que recorrer un circulo
     de ~0.44 palmas de radio y hacerlo en sentido horario visto de frente.
     Se muestrea la animacion real durante una vuelta y se mide el recorrido.
"""
import json
import math
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from pose_lab_e import HAND_POS_JS, free_camera
from pose_lab_q import MEASURE_JS
from pose_lab_q2 import apertura, cam
from movimiento_q import POS_JS
import search_e9 as se9
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "verify_q"
OUT.mkdir(parents=True, exist_ok=True)

se9.URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=vq"

# Lo que tiene que cumplirse para que se lea una Q y no una G ni una D.
CRITERIOS = {
    "idxAng": (-152.0, -118.0),   # indice hacia abajo y a la izquierda
    "thAng": (-118.0, -88.0),     # pulgar colgando
    "pico": (24.0, 44.0),         # apertura del pico en pantalla
    "sep": (0.95, 1.40),          # separacion de yemas, en palmas
    "punoMax": (0.0, 0.80),       # medio, anular y menique recogidos
}
TRAZO = {
    "radio": (0.34, 0.54),        # radio del circulo, en palmas
    "vuelta": (330.0, 390.0),     # grados recorridos en un periodo completo
    "ovalo": (0.0, 0.35),         # diferencia relativa entre ancho y alto
}

VISTAS = {
    "produccion": ("0m 2.45m 0.15m", "0deg 84deg 2.5m", "30deg", 0.0),
    "mano": (None, "0deg 84deg 1.00m", "21deg", -0.04),
    "perfil": (None, "-55deg 84deg 0.80m", "24deg", -0.04),
}


def rango(nombre, valor, lo, hi):
    bien = lo <= valor <= hi
    print(f"  {nombre:10s} {valor:+8.2f}  [{lo}, {hi}]  {'ok' if bien else 'FALLA'}")
    return bien


def periodo():
    """Duracion de una vuelta completa del ciclo, en segundos."""
    catalogo = json.loads((ROOT / "data" / "catalogo-lsm.json").read_text("utf-8"))
    c = next(s for s in catalogo["senas"] if s["letra"] == "Q")["ciclo"]
    return sum(c[k] for k in ("holdStartMs", "durationMs", "holdEndMs", "resetMs")) / 1000


def main():
    ciclo_s = periodo()
    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 1100, "height": 900})
        time.sleep(0.3)
        viewer = page.query_selector("#viewer")

        page.evaluate("() => window.__LSM_CONTROLLER__.mostrarSena('Q')")
        # la transicion dura 2 s y el ciclo espera holdStartMs antes de arrancar
        time.sleep(2.6)

        m = page.evaluate(MEASURE_JS)
        medidas = {
            "idxAng": m["idxAng"],
            "thAng": m["thAng"],
            "pico": apertura(m),
            "sep": m["pico"],
            "punoMax": m["punoMax"],
        }
        print("forma de la Q:")
        ok = all(rango(k, medidas[k], *CRITERIOS[k]) for k in CRITERIOS)

        # --- el trazo: se muestrea la animacion real durante una vuelta -----
        # la ventana es exactamente un periodo del ciclo: asi da igual en que
        # punto del recorrido se empiece, el giro acumulado tiene que ser 360
        puntos = []
        fin = time.time() + ciclo_s
        while time.time() < fin:
            q = page.evaluate(POS_JS)
            puntos.append((q["x"] / q["palm"], q["y"] / q["palm"]))
        xs = [q[0] for q in puntos]
        ys = [q[1] for q in puntos]
        cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
        radios = [math.hypot(x - cx, y - cy) for x, y in puntos]
        radio = sum(radios) / len(radios)
        ancho, alto = max(xs) - min(xs), max(ys) - min(ys)
        ovalo = abs(ancho - alto) / max(ancho, alto, 1e-6)

        # grados recorridos: se acumula el giro entre muestras consecutivas,
        # con signo, para distinguir una vuelta de un vaiven
        angs = [math.degrees(math.atan2(y - cy, x - cx)) for x, y in puntos]
        vuelta = 0.0
        for a, b in zip(angs, angs[1:]):
            d = (b - a + 180) % 360 - 180
            vuelta += d
        print(f"\ntrazo ({len(puntos)} muestras en {ciclo_s:.2f} s de ciclo):")
        ok &= rango("radio", radio, *TRAZO["radio"])
        ok &= rango("vuelta", abs(vuelta), *TRAZO["vuelta"])
        ok &= rango("ovalo", ovalo, *TRAZO["ovalo"])
        sentido = "horario" if vuelta < 0 else "antihorario"
        print(f"  sentido    {sentido:>8s}            [horario]  "
              f"{'ok' if vuelta < 0 else 'FALLA'}")
        ok &= vuelta < 0

        print("\n  " + ("TODO OK" if ok else "REVISAR"))
        print("  rotulo:", page.inner_text("#anim-info").strip()[:120])

        free_camera(page)
        mano = page.evaluate(HAND_POS_JS)
        for nombre, (target, orbit, fov, dy) in VISTAS.items():
            t = target or "%.3fm %.3fm %.3fm" % (
                mano["x"], mano["y"] + dy, mano["z"]
            )
            cam(page, t, orbit, fov)
            viewer.screenshot(path=str(OUT / f"Q_{nombre}.png"))

        browser.close()
    print("Capturas en", OUT)


if __name__ == "__main__":
    main()
