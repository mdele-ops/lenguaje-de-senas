"""T: buscar la pose puntuando la SILUETA del render, no los huesos.

Las dos vueltas anteriores (`search_t.py` y `afina_t.py`) llegaron a puntuacion
casi cero y a un render donde el pulgar no se ve: `camCima` mide huesos y la
lamina esta medida sobre carne, asi que perseguir el numero de la lamina con el
numero del hueso deja el pulgar medio dedo mas abajo de lo que hace falta.

Aqui cada candidata se DIBUJA y se mide sobre lo dibujado (`silueta_t`):

  asoma   cuanto sube la mano por encima del puno sin pulgar. En la lamina
          vale 0.09 anchos de puno; ahi es donde tiene que caer.
  xCima   en que columna esta ese punto mas alto. Tiene que ser la muesca
          entre el indice y el medio, no el costado del indice.
  ancho   lo ancho que se ve lo que asoma. Un pulgar es un pellizco (~0.17 de
          puno en la lamina); si sale medio puno, es que se abrio el abanico.

Del laboratorio de huesos se conservan solo los guardas que la camara no ve:
que las mallas no se atraviesen, que el pulgar no se doble sobre si mismo y
que el puno siga cerrado.

Se mide con la camara pegada a la mano, no con la de la aplicacion: en el
encuadre de la app el puno ocupa 88 pixeles de ancho, y sobre 88 pixeles un
"asoma" de 0.10 son nueve, con lo que la medida es casi todo ruido. Pegada, el
puno pasa de 300 y ademas el campo de vision estrecho se parece mas al de la
lamina, que es una foto de lejos. Las tres medidas van divididas por el ancho
del puno, asi que no dependen del tamano de la captura.
"""
import io
import json
import time
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

from lupa_t import FOV, MUESCA_JS
from mira_t import PUNTOS_JS, abrir_nitido
from pose_lab_e import free_camera
from pose_lab_t import MEASURE_JS
from search_t import GAP_MIN, construye
from silueta_t import mide
import search_e9 as se9

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "busca_t"
OUT.mkdir(parents=True, exist_ok=True)

se9.URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=t12"

PARTIDA = {"tcurl": 0.35, "t1x": -55, "t1z": 56, "t1y": 30,
           "t2x": 0, "t3x": -5, "sep": 16}

# Mismo puno, pulgar apartado del hueco: es el contorno contra el que se mide
# cuanto asoma. Los dedos no se tocan, asi que vale para todas las candidatas.
FUERA = {"tcurl": 0.55, "t1x": 40, "t1z": -30, "t1y": -20, "t2x": 20, "t3x": 20}

RANGOS = {
    "tcurl": [round(0.05 * i, 2) for i in range(0, 11)],
    "t1x": list(range(-80, -29, 5)),
    "t1z": list(range(20, 86, 5)),
    "t1y": list(range(-30, 61, 10)),
    "t2x": list(range(-40, 41, 10)),
    "t3x": list(range(-40, 41, 10)),
    "sep": list(range(6, 25, 2)),
}
VUELTAS = 3

# Lo que dice la lamina, medido sobre la lamina (ver `medida_t.py`).
META_ASOMA = 0.10
META_DESVIO = 0.00
ANCHO_OK = (0.08, 0.32)


ORBIT = "0deg 84deg 1.05m"


def cam(page, centro):
    page.evaluate(
        """(a) => {
            const mv = document.getElementById('handViewer');
            mv.cameraTarget = a.t;
            mv.cameraOrbit = a.orbit;
            mv.fieldOfView = a.fov;
            mv.jumpCameraToGoal();
        }""",
        {"t": "%.4fm %.4fm %.4fm" % tuple(centro), "orbit": ORBIT, "fov": FOV},
    )
    time.sleep(0.4)


def marco(page, im):
    """Columnas del puno y ancho del puno, en pixeles de la captura."""
    datos = page.evaluate(PUNTOS_JS, [
        "mixamorig1RightHandIndex1_040", "mixamorig1RightHandPinky1_052",
        "mixamorig1RightHandMiddle1_044",
    ])
    ex = im.width / datos["w"]
    xi = datos["pts"]["mixamorig1RightHandIndex1_040"][0] * ex
    xp = datos["pts"]["mixamorig1RightHandPinky1_052"][0] * ex
    xm = datos["pts"]["mixamorig1RightHandMiddle1_044"][0] * ex
    ancho = abs(xi - xp)
    # margen a los lados: el pulgar puede asomar por fuera del indice
    x0 = int(max(0, min(xi, xp) - 0.35 * ancho))
    x1 = int(min(im.width, max(xi, xp) + 0.35 * ancho))
    return {"x0": x0, "x1": x1, "ancho": ancho, "xMuesca": (xi + xm) / 2}


def puntua(m, s, mar):
    """Cuanto se aparta del dibujo de la lamina."""
    d = {}
    # 1. que el pulgar ASOME, y lo que asoma en la lamina
    d["asoma"] = 26 * abs(s["asoma"] - META_ASOMA)
    # 2. y que asome por la muesca, no por el costado del indice
    d["desvio"] = 22 * abs((s["xCima"] - mar["xMuesca"]) / mar["ancho"] - META_DESVIO)
    # 3. un pellizco de pulgar, no un quinto dedo ni medio puno
    d["ancho"] = 10 * (max(0.0, ANCHO_OK[0] - s["ancho"])
                       + max(0.0, s["ancho"] - ANCHO_OK[1]))
    # --- guardas que la camara no ve ---------------------------------------
    d["gap"] = 60 * (max(0.0, GAP_MIN - m["gapIdxPunta"])
                     + max(0.0, GAP_MIN - m["gapMedPunta"]))
    d["base"] = 25 * max(0.0, 0.075 - m["gapBase"])
    d["dobla"] = 0.05 * max(0.0, m["dobla"] - 95)
    d["puno"] = 8 * max(0.0, m["punoMax"] - 0.78)
    d["abanico"] = 8 * (max(0.0, m["huecoMR"] - 0.30)
                        + max(0.0, m["huecoRP"] - 0.30))
    return sum(d.values()), d


def linea(nombre, m, s, mar, p):
    return (
        f"{nombre:24s} p={p:6.2f} asoma={s['asoma']:+.3f} "
        f"desv={(s['xCima'] - mar['xMuesca']) / mar['ancho']:+.3f} "
        f"ancho={s['ancho']:.3f} gIp={m['gapIdxPunta']:.3f} "
        f"gMp={m['gapMedPunta']:.3f} dobla={m['dobla']:5.1f}"
    )


def main():
    receta = dict(PARTIDA)

    with sync_playwright() as p:
        browser, page = abrir_nitido(p, lado=760, escala=2)
        free_camera(page)

        def dibuja(r):
            page.evaluate(
                "(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", construye(r)
            )
            page.evaluate(
                "() => new Promise((r) => requestAnimationFrame("
                "() => requestAnimationFrame(r)))"
            )
            # En memoria y no a disco: con la captura en un fichero fijo, la
            # siguiente candidata lo pisaba antes de que PIL lo hubiera leido
            # (PIL abre en diferido) y reventaba a media busqueda.
            return Image.open(io.BytesIO(
                page.query_selector("#handViewer").screenshot()
            ))

        # El encuadre se fija UNA vez: si la camara se moviera entre capturas,
        # restar una silueta de otra no querria decir nada.
        page.evaluate(
            "(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", construye(receta)
        )
        time.sleep(0.4)
        centro = page.evaluate(MUESCA_JS)
        cam(page, centro)

        # El fondo depende del abanico de los dedos, y `sep` es uno de los
        # mandos que se mueven: hay que tener un fondo por cada valor de sep, o
        # las medidas se comparan contra un puno que ya no es el mismo.
        fondos = {}

        def fondo_de(sep):
            if sep not in fondos:
                im = dibuja(dict(receta, sep=sep, **FUERA))
                im.save(OUT / f"_sin_pulgar_sep{sep}.png")
                fondos[sep] = (im, marco(page, im))
            return fondos[sep]

        print("  marco:", {k: round(v, 1) for k, v in fondo_de(receta["sep"])[1].items()})

        def evalua(r):
            fondo, mar = fondo_de(r["sep"])
            im = dibuja(r)
            m = page.evaluate(MEASURE_JS)
            s = mide(fondo, im, mar["x0"], mar["x1"], mar["ancho"])
            if s is None or m.get("error"):
                return None
            pts, det = puntua(m, s, mar)
            return pts, det, m, s, mar

        base = evalua(receta)
        mejor = base[0]
        print(" ", linea("partida", base[2], base[3], base[4], mejor))

        for vuelta in range(VUELTAS):
            movio = False
            for mando, valores in RANGOS.items():
                actual = receta[mando]
                elegido = actual
                for v in valores:
                    if v == actual:
                        continue
                    receta[mando] = v
                    res = evalua(receta)
                    if res and res[0] < mejor - 1e-9:
                        mejor, elegido = res[0], v
                receta[mando] = elegido
                if elegido != actual:
                    movio = True
                    print(f"  v{vuelta+1} {mando:6s} {actual} -> {elegido}"
                          f"  p={mejor:.3f}")
            if not movio:
                print(f"  vuelta {vuelta+1}: nada que mejorar, se para")
                break

        pts, det, m, s, mar = evalua(receta)
        dibuja(receta).save(OUT / "_final.png")
        print("\n ", linea("final", m, s, mar, pts))
        print("  receta:", receta)
        print("  castigos:", {k: round(v, 3) for k, v in det.items() if v > 1e-6})

        browser.close()

    (OUT / "_final.json").write_text(
        json.dumps({"receta": receta, "puntos": pts, "detalle": det,
                    "silueta": s, "medidas": m, "marco": mar}, indent=2),
        "utf-8",
    )
    print("Datos en", OUT)


if __name__ == "__main__":
    main()
