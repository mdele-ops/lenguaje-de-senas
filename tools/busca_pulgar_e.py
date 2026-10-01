"""Busqueda del pulgar de la E con los dedos ya calibrados y fijos.

El pulgar no cambia los angulos de los cuatro dedos, asi que se calibra una sola
vez y despues se recorren los pulgares sobre esa misma base. Se puntua con
`pulgar_e.puntuar`, que mide TODAS las articulaciones del pulgar contra el marco
de la palma y no solo la punta.

Son siete grados de libertad: una rejilla con paso util no cabe (una de 4 pasos
por eje ya son 16384 poses). Se hace muestreo al azar sobre los rangos y luego
un afinado local alrededor del mejor, que en siete dimensiones cubre mucho mas
espacio por evaluacion que la rejilla.
"""
import json
import random
from pathlib import Path

from playwright.sync_api import sync_playwright

from calibra_e import PULGAR, calibrar, pose, pulgar
from pulgar_e import PULGAR_JS, linea, puntuar
from search_e9 import abrir
from search_e10 import CAM_PROD_JS
from simetria_e import SIMETRIA_JS, informe

ROOT = Path(__file__).resolve().parents[1]
# reparto elegido en reparto_e.py: deja la yema a 0.21 de palma bajo los
# nudillos y ligeramente por delante, como en la foto
DEDOS = {"mcp": 70.0, "pip": 95.0, "dip": 90.0}
CONV = 8
MUESTRAS = 5000
AFINADOS = 2000

# Rangos amplios a proposito. Cada vez que se han apretado, el mejor candidato
# ha salido pegado a un tope -senal de que el optimo estaba fuera- y la
# busqueda ha tenido que conformarse con lo que habia dentro.
EJES = (
    ("tcurl", 0.00, 1.00),
    ("aside", -1.00, 1.00),
    ("t1x", -60, 90),
    ("t1y", -80, 60),
    ("t1z", -60, 120),
    # Los dos ultimos van cortos a proposito. Sus grados se SUMAN a los del
    # `curl`, asi que en cuanto se les da cuerda cierran el pulgar en anillo;
    # aqui solo tienen que poder retocar, no doblar el dedo.
    ("t2x", -30, 40),
    ("t3x", -25, 30),
)


def como_pulgar(v):
    d = dict(zip([e[0] for e in EJES], v))
    return pulgar(
        round(d["tcurl"], 2), round(d["aside"], 2),
        t1={"x": round(d["t1x"]), "y": round(d["t1y"]), "z": round(d["t1z"])},
        t2={"x": round(d["t2x"])},
        t3={"x": round(d["t3x"])},
    )


def etiqueta(v):
    return " ".join(
        f"{nombre}{round(val, 2)}" for (nombre, _, _), val in zip(EJES, v)
    )


def distintos(res, cuantos, minimo=0.18):
    """Quita las variantes casi identicas: el afinado local devuelve decenas de
    copias del mismo pulgar y en la hoja de contactos no aportan nada."""
    salida, vistos = [], []
    for sc, v, m in res:
        norm = [(val - lo) / (hi - lo) for val, (_, lo, hi) in zip(v, EJES)]
        lejos = all(
            max(abs(a - b) for a, b in zip(norm, otro)) > minimo for otro in vistos
        )
        if lejos:
            vistos.append(norm)
            salida.append((sc, v, m))
            if len(salida) >= cuantos:
                break
    return salida


def main():
    rnd = random.Random(7)

    with sync_playwright() as p:
        browser, page = abrir(p)
        # parte del pulgar se puntua en pantalla, asi que la camara tiene que
        # ser siempre la misma y la de la app
        page.evaluate(CAM_PROD_JS)

        def aplicar(pz):
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pz)

        def sim(pz):
            aplicar(pz)
            return page.evaluate(SIMETRIA_JS)

        def pul(pz):
            aplicar(pz)
            return page.evaluate(PULGAR_JS)

        corr, s = calibrar(sim, 0.0, CONV, objetivo=DEDOS, verbose=False)
        print("dedos calibrados:", informe("", s))
        m0 = pul(pose(0.0, CONV, corr, PULGAR))
        print("pulgar actual   ", linea("refine_e14", m0, puntuar(m0)), "\n")

        def evaluar(v):
            m = pul(pose(0.0, CONV, corr, como_pulgar(v)))
            return puntuar(m), m

        print(f"muestreo al azar: {MUESTRAS}")
        res = []
        for _ in range(MUESTRAS):
            v = [rnd.uniform(lo, hi) for _, lo, hi in EJES]
            sc, m = evaluar(v)
            res.append((sc, v, m))
        res.sort(key=lambda t: t[0])
        print("  mejor del muestreo:", linea(etiqueta(res[0][1]), res[0][2], res[0][0]))

        print(f"afinado local: {AFINADOS}")
        mejor = res[0]
        radio = 0.35
        for i in range(AFINADOS):
            if i and i % (AFINADOS // 5) == 0:
                radio *= 0.55
            v = [
                min(hi, max(lo, mejor[1][j] + rnd.gauss(0, radio * (hi - lo) / 2)))
                for j, (_, lo, hi) in enumerate(EJES)
            ]
            sc, m = evaluar(v)
            if sc < mejor[0]:
                mejor = (sc, v, m)
            res.append((sc, v, m))
        res.sort(key=lambda t: t[0])
        res = distintos(res, 12)

        print("MEJORES (ya filtrados por variedad)")
        for sc, v, m in res:
            print(" ", linea(etiqueta(v), m, sc))
        browser.close()

    out = ROOT / "tools" / "screenshots" / "busca_pulgar_e.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(
            {
                "dedos": DEDOS,
                "conv": CONV,
                "correcciones": corr,
                "mejores": [
                    {"score": sc, "pulgar": como_pulgar(v), "m": m}
                    for sc, v, m in res
                ],
            },
            indent=2,
        ),
        "utf-8",
    )
    print("\n->", out)


if __name__ == "__main__":
    main()
