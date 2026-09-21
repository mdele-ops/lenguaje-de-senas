"""Escribe en el catalogo la E corregida y deja el antes/despues para revisarla.

Que cambia respecto a la version anterior y por que:

1. Los cuatro dedos doblan lo mismo. Con `curl` igual en los cuatro salian
   angulos distintos, porque el reposo del .glb no es simetrico; la ultima
   falange se iba 27 grados entre el indice y el anular y la fila de yemas
   quedaba escalonada. Ahora el `curl` sigue haciendo el trabajo grueso y
   encima va un retoque por falange, calculado midiendo el modelo
   (`calibra_e.py`), que iguala mcp/pip/dip en los cuatro dedos.

2. El puno se cierra de verdad. El reparto anterior (mcp 70 / pip 95 / dip 60)
   dejaba las yemas a 0.51 de palma por debajo de los nudillos: el dedo bajaba
   arrastrandose por la palma y se leia como una garra. En la foto la yema se
   queda a 0.21, o sea el dedo se enrolla sobre si mismo. Con dip 90 se llega
   a 0.21 (`reparto_e.py`).

3. Los dedos se tocan, como en la foto, en vez de ir abiertos en abanico.

4. El pulgar queda HORIZONTAL, como una barra corta justo debajo de las yemas,
   con las puntas de los cuatro dedos apoyadas encima. Es la forma de la
   lamina de referencia del proyecto, y las dos versiones anteriores no la
   daban: la primera lo sacaba por el costado como un cuerno, la segunda lo
   cerraba en anillo, y la tercera -solo `curl` y `aside`- lo dejaba en una
   diagonal larga cruzando la palma entera.

   La orientacion NO se puede conseguir solo con `curl`/`aside`: esos dos
   mandos dejan el pulgar a unos 48 grados y no lo tumban mas. Hace falta
   girar la base (`Thumb1`), que orienta el dedo entero sin doblarlo. Lo que
   si hay que evitar es cargar `Thumb2`/`Thumb3`, porque sus grados se SUMAN
   a los del curl y son los que cerraron el anillo; aqui van en 24 y -11, y
   el pulgar entero se dobla 87 grados sobre si mismo, por debajo del umbral
   de ~90 en que empieza a verse el agujero.
"""
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from calibra_e import calibrar, pose, pulgar
from hoja_e import preparar, publicar, retratar
from pose_lab_e import T1, T2, T3
from pulgar_e import PULGAR_JS
from pulgar_e import linea as linea_pulgar
from pulgar_e import puntuar as puntuar_pulgar
from search_e9 import abrir
from simetria_e import SIMETRIA_JS, detalle, informe

ROOT = Path(__file__).resolve().parents[1]
CATALOGO = ROOT / "data" / "catalogo-lsm.json"
OUT = ROOT / "tools" / "screenshots" / "final_e15"

# El curl hace el grueso del cierre y el retoque por falange solo lo iguala,
# asi la pose sigue leyendose como "puno" y no como 12 angulos sueltos.
CURL = 0.92
CONV = 8
OBJETIVO = {"mcp": 70.0, "pip": 95.0, "dip": 90.0}

# Ganador de busca_pulgar_e.py, rematado con el barrido de escalera_pulgar_e.py
# comparando contra la lamina.
PULGAR_E = pulgar(
    0.59, -0.96,
    t1={"x": 60, "y": -35, "z": 78},
    t2={"x": 24},
    t3={"x": -11},
)

DESCRIPCION = (
    "Pu\u00f1o compacto con la palma al frente: los cuatro dedos, juntos y "
    "doblados por igual, se enrollan hasta que las yemas quedan justo debajo "
    "de los nudillos; el pulgar cruza la palma tumbado y en horizontal, justo "
    "por debajo de las yemas, que se apoyan encima de \u00e9l."
)

VISTAS = {
    "frente": ("0deg 84deg 0.95m", "22deg"),
    "lado": ("-62deg 84deg 0.95m", "22deg"),
    "abajo": ("0deg 112deg 0.95m", "22deg"),
}


ORDEN = ("thumb", "index", "middle", "ring", "pinky", "muneca", "extra")
MINIMO = 1.5  # grados: por debajo de esto el retoque no se ve y solo ensucia


def grados(v):
    """Entero si es redondo; un decimal si no."""
    v = round(v, 1)
    return int(v) if v == int(v) else v


def limpiar(pz):
    """Deja la pose legible: orden anatomico, sin retoques irrelevantes."""
    extra = {}
    for hueso in orden_huesos(pz.get("extra", {})):
        rot = {
            eje: grados(g)
            for eje, g in pz["extra"][hueso].items()
            if abs(g) >= MINIMO
        }
        if rot:
            extra[hueso] = rot

    out = {}
    for clave in ORDEN:
        if clave == "extra":
            if extra:
                out["extra"] = extra
        elif clave in pz:
            out[clave] = {
                k: (grados(v) if k == "spread" else round(v, 2))
                for k, v in pz[clave].items()
            }
    return out


def orden_huesos(extra):
    """Pulgar, luego indice-medio-anular-menique, y el brazo al final."""
    cadena = [T1, T2, T3] + [
        f"mixamorig1RightHand{n}"
        for n in (
            "Index1_040", "Index2_041", "Index3_042",
            "Middle1_044", "Middle2_045", "Middle3_046",
            "Ring1_048", "Ring2_049", "Ring3_050",
            "Pinky1_052", "Pinky2_053", "Pinky3_054",
        )
    ]
    rango = {nombre: i for i, nombre in enumerate(cadena)}
    return sorted(extra, key=lambda n: (rango.get(n, len(cadena)), n))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cat = json.loads(CATALOGO.read_text("utf-8"))
    sena = next(x for x in cat["senas"] if x["letra"] == "E")
    anterior = json.loads(json.dumps(sena["pose"]))

    with sync_playwright() as p:
        browser, page = abrir(p)
        viewer = preparar(page)

        def aplicar(pz):
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pz)
            time.sleep(0.35)

        def sim(pz):
            aplicar(pz)
            return page.evaluate(SIMETRIA_JS)

        salida = {}
        s = sim(anterior)
        m = page.evaluate(PULGAR_JS)
        print("ANTES ", informe("E", s))
        print(detalle(s))
        print("      ", linea_pulgar("pulgar", m, puntuar_pulgar(m)), "\n")
        retratar(page, viewer, "1_ANTES", OUT, salida, vistas=VISTAS)

        corr, _ = calibrar(
            sim, CURL, CONV, objetivo=OBJETIVO, verbose=False, thumb=PULGAR_E
        )
        nueva = limpiar(pose(CURL, CONV, corr, PULGAR_E))

        s = sim(nueva)
        m = page.evaluate(PULGAR_JS)
        print("DESPUES", informe("E", s))
        print(detalle(s))
        print("      ", linea_pulgar("pulgar", m, puntuar_pulgar(m)))
        retratar(page, viewer, "2_DESPUES", OUT, salida, vistas=VISTAS)
        browser.close()

    sena["pose"] = nueva
    sena["descripcion"] = DESCRIPCION
    partes = cat["version"].split(".")
    partes[-1] = str(int(partes[-1]) + 1)
    cat["version"] = ".".join(partes)
    CATALOGO.write_text(
        json.dumps(cat, ensure_ascii=False, indent=2) + "\n", "utf-8"
    )
    print("\ncatalogo ->", CATALOGO, "version", cat["version"])

    publicar(salida, OUT, cols=3, cell=320)
    (OUT / "_pose.json").write_text(
        json.dumps({"antes": anterior, "despues": nueva}, indent=2), "utf-8"
    )


if __name__ == "__main__":
    main()
