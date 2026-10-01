"""T busqueda 1: rejilla sobre los mandos que meten el pulgar en el hueco.

Del lab 1 salen los ejes que sirven y para que sirve cada uno:

  T1.z (+)  es el que CRUZA el pulgar hacia el hueco indice-medio. Con +30 la
            yema ya cae en el hueco (desvio +0.04) pero pegada al indice
            (gapIdx 0.057, o sea las mallas se atraviesan).
  T1.x (-)  es el que lo PONE DE PIE y lo mete hacia dentro del puno: con -60
            thUpDir sube a 0.93 y sobreFrente pasa de +0.39 a -0.42.
  tcurl (-) menos curl = pulgar mas estirado y mas alto (cima -0.07 con 0.1).
  spread indice/medio  es lo unico que abre el hueco: con indice -16 y medio
            +16 el hueco pasa de 0.222 a 0.261. Sin abrirlo el pulgar no cabe.

Asi que la pose no es un mando, son cuatro a la vez, y se buscan en rejilla.
Se puntua en PANTALLA (camDesvio, camCima) porque eso es lo que el usuario
juzga, y en 3D lo que no se ve: que las mallas no se atraviesen.

Lo que enseño la primera vuelta (ver `ojo_t.py`): no vale con dejar la yema
DENTRO del hueco. El hueco entre indice y medio mide 0.22-0.26 de palma y el
pulgar es igual de gordo, asi que metido ahi la carne se queda enterrada: el
esqueleto decia "yema arriba y en medio" y en el render no habia ningun pulgar,
solo un pellizco en la malla. El pulgar tiene que ir APOYADO EN EL FRENTE del
puno, como en la S (sobreFrente ~ 0.17), y lo que cambia respecto a la S es
donde para y como mira: la S sigue de largo hasta el anular y va tumbada; la T
se queda en la muesca indice-medio y va de pie.
"""
import itertools
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from pose_lab_e import T1, T2, T3, free_camera
from pose_lab_t import MEASURE_JS, pose_t
from ver_s import CAM_FOV, CAM_ORBIT, CAM_TARGET
import search_e9 as se9
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "search_t"
OUT.mkdir(parents=True, exist_ok=True)

se9.URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=t2"

# Los huesos van por el centro de la carne, asi que dos cadenas muy juntas
# tienen las mallas metidas una en otra. El umbral no se inventa: `estado_t.py`
# lo mide en las letras que ya pasaron revision. La E, con el pulgar apoyado
# debajo de las yemas, vive en 0.086-0.124, asi que ahi todavia no hay problema
# visible; por debajo de ~0.09 si.
GAP_MIN = 0.095


def construye(r):
    return pose_t(
        tcurl=r["tcurl"],
        thumb={
            T1: {"x": r["t1x"], "y": r["t1y"], "z": r["t1z"]},
            T2: {"x": r["t2x"]},
            T3: {"x": r["t3x"]},
        },
        spread=(-r["sep"], r["sep"], 0, 0),
    )


# Lo que tiene que dar la pose. Los rangos salen de la lamina y de lo que
# `estado_t.py` mide en las letras ya aceptadas:
#
#   letra   camDesvio  camCima  sobreFrente   thUpDir
#   A         -0.28     -0.68      0.42        0.31   pulgar de pie, al costado
#   S         +0.66     -0.22      0.17        0.41   tumbado, cruzando entero
#   E         +0.75     -0.82     -0.48       -0.08   horizontal, bajo las yemas
#   T (meta)   0.00     +0.05      0.12..0.45  >0.5   de pie, en la muesca
#
# Visto asi la T es la A con el pulgar movido de sitio: la misma manera de
# estar de pie y por delante del puno, pero la yema corrida ~0.28 de ancho de
# puno hacia el medio y subida hasta asomar por encima de los nudillos.
# Estos dos no son a ojo: `medida_t.py` los mide sobre la lamina. Son
# adimensionales (van divididos por el ancho del puno), asi que valen igual en
# la foto que en el modelo y se pueden perseguir como valor exacto, no como
# rango: puestos en banda la busqueda se planta en cuanto entra y deja de
# mejorar.
META = {"camDesvio": -0.010, "camCima": 0.108}

# El resto si van en banda: no hay un valor "correcto", solo un intervalo
# fuera del cual la letra deja de leerse.
OBJETIVO = {
    "sobreFrente": (0.12, 0.45),   # por delante del puno, como en la A
    "thUpDir": (0.50, 1.00),       # de pie (la S va en 0.41)
    "thLatDir": (-0.20, 0.55),     # sin cruzar el puno entero como la S
}


def puntua(m):
    """Cuanto se aparta de la lamina. 0 seria clavarla; se suman castigos.

    El orden importa: primero que la letra EXISTA (la yema en la muesca,
    asomando y con carne visible), despues que no se atraviesen las mallas, y
    al final los detalles.
    """
    detalle = {}
    fuera = lambda k, lo, hi: max(0.0, lo - m[k]) + max(0.0, m[k] - hi)

    # 1. la yema, en pantalla, en la muesca entre indice y medio
    detalle["desvio"] = 30 * abs(m["camDesvio"] - META["camDesvio"])
    # 2. asomando por encima del puno lo mismo que en la lamina
    detalle["cima"] = 14 * abs(m["camCima"] - META["camCima"])
    # 3. apoyada en el frente del puno: metida a ras, la carne no se ve
    detalle["frente"] = 14 * fuera("sobreFrente", *OBJETIVO["sobreFrente"])
    # 4. de pie y sin cruzar de largo: es lo que la separa de la S
    detalle["dePie"] = 6 * fuera("thUpDir", *OBJETIVO["thUpDir"])
    detalle["cruza"] = 5 * fuera("thLatDir", *OBJETIVO["thLatDir"])
    # 5. sin atravesar indice ni medio con la parte que se ve. La base del
    #    pulgar y la del indice van juntas en cualquier mano, tambien en la
    #    lamina, asi que esa no se castiga: solo se pide que no se hunda.
    detalle["gap"] = 60 * (
        max(0.0, GAP_MIN - m["gapIdxPunta"]) + max(0.0, GAP_MIN - m["gapMedPunta"])
    )
    detalle["base"] = 25 * max(0.0, 0.075 - m["gapBase"])
    # 5b. ENTRE los dos dedos, no pegado al indice. Sin esto salen poses con la
    #     yema en el sitio pero el pulgar montado sobre el indice, que de frente
    #     se leen como un dedo mas y no como una T.
    detalle["simetria"] = 8 * max(0.0, m["simetria"] - 0.06)
    # 6. sin doblarse sobre si mismo (el anillo de la E)
    detalle["dobla"] = 0.05 * max(0.0, m["dobla"] - 95)
    # 7. puno cerrado y abanico sin abrirse de mas
    detalle["puno"] = 8 * max(0.0, m["punoMax"] - 0.78)
    detalle["abanico"] = 8 * (
        max(0.0, m["huecoMR"] - 0.30) + max(0.0, m["huecoRP"] - 0.30)
    )

    return sum(detalle.values()), detalle


def linea(nombre, m, p):
    return (
        f"{nombre:26s} p={p:6.2f} desv={m['camDesvio']:+6.3f} "
        f"cima={m['camCima']:+6.3f} sobre={m['sobreFrente']:+6.3f} "
        f"gIp={m['gapIdxPunta']:.3f} gMp={m['gapMedPunta']:.3f} "
        f"base={m['gapBase']:.3f} "
        f"up={m['thUpDir']:+5.2f} lat={m['thLatDir']:+5.2f} "
        f"dobla={m['dobla']:5.1f}"
    )


REJILLA = {
    "tcurl": (0.0, 0.15, 0.30),
    "t1x": (-50, -30, -10, 10),
    "t1z": (20, 32, 44, 56),
    "t1y": (-30, 0, 30),
    "t2x": (-30, 0, 30),
    "t3x": (-30, 0),
    "sep": (10,),
}


def cam(page):
    page.evaluate(
        """(a) => {
            const mv = document.getElementById('handViewer');
            mv.cameraTarget = a.t;
            mv.cameraOrbit = a.orbit;
            mv.fieldOfView = a.fov;
            mv.jumpCameraToGoal();
        }""",
        {"t": CAM_TARGET, "orbit": CAM_ORBIT, "fov": CAM_FOV},
    )
    time.sleep(0.25)


def main():
    claves = list(REJILLA)
    combos = list(itertools.product(*(REJILLA[k] for k in claves)))
    print(f"{len(combos)} combinaciones")

    resultados = []
    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 900, "height": 900})
        time.sleep(0.4)
        free_camera(page)
        cam(page)

        for i, combo in enumerate(combos):
            r = dict(zip(claves, combo))
            page.evaluate(
                "(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", construye(r)
            )
            time.sleep(0.05)
            m = page.evaluate(MEASURE_JS)
            if m.get("error"):
                continue
            pts, detalle = puntua(m)
            resultados.append({"receta": r, "puntos": pts, "detalle": detalle, "m": m})
            if (i + 1) % 100 == 0:
                print(f"  {i+1}/{len(combos)}")

        browser.close()

    resultados.sort(key=lambda x: x["puntos"])
    print("\nmejores:")
    for r in resultados[:20]:
        nombre = "_".join(f"{k}{r['receta'][k]}" for k in claves)
        print(" ", linea(nombre, r["m"], r["puntos"]))

    (OUT / "_top.json").write_text(
        json.dumps(resultados[:60], indent=2), "utf-8"
    )
    print("\nDatos en", OUT)


if __name__ == "__main__":
    main()
