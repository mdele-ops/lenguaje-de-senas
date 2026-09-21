"""Variantes de la O con el arco mas o menos cerrado, cada una con su pulgar.

El afinado da UNA respuesta, la que minimiza la puntuacion, pero la puntuacion
no sabe cuanto agujero se ve bonito: eso se elige mirando. Aqui se fija el
arco de los dedos en varios valores y, para cada uno, se vuelve a buscar el
pulgar que mejor lo cierra, de modo que la hoja compare formas de O de verdad
y no una O buena contra varias mal cerradas.
"""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

from afina_o import MANDOS_PULGAR, Medidor, descenso
from calibra_o import calibrar, limpiar
from medida_o import linea, metricas
from pose_o import dedos, juntar, pulgar
from retrato_o import ARM_Z, pose_catalogo, retratar
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
AFINADA = ROOT / "tools" / "screenshots" / "afina_o.json"
OUT = ROOT / "tools" / "screenshots" / "variantes_o"

MUNECA = {"y": 70}

# mcp / pip / dip objetivo de cada variante, de aro grande a aro pequeno
ARCOS = {
    "A_abierta": (52, 50, 26),
    "B_media": (59, 57, 30),
    "C_cerrada": (66, 66, 34),
    "D_muycerrada": (72, 76, 38),
    # mas doblez en la falange media: la yema apunta al pulgar en vez de
    # alargarse hacia afuera, que es lo que redondea el agujero
    "E_yemas": (56, 78, 34),
    "F_yemas_mas": (50, 90, 40),
}


def construir(kd, kp, muneca=MUNECA):
    return juntar(
        dedos(**kd),
        pulgar(
            kp["curl"], kp["aside"],
            t1={"x": kp["t1x"], "y": kp["t1y"], "z": kp["t1z"]},
            t2x=kp["t2x"], t3x=kp["t3x"],
        ),
        muneca=muneca,
        arm_z=ARM_Z,
    )


def main():
    semilla = json.loads(AFINADA.read_text("utf-8"))
    kp0 = semilla["pulgar"]
    recetas = {}

    with sync_playwright() as p:
        browser, page = abrir(p)
        med = Medidor(page)
        for nombre, (mcp, pip, dip) in ARCOS.items():
            # todo el doblez sale de la correccion, asi el arco cae exacto
            base = {"curl": 0.0, "mcp": 0, "pip": 0, "dip": 0, "fan": 0}
            corr, _ = calibrar(
                lambda kw: metricas({**med.dedos(kw), **med.pulgar(kp0)}),
                base,
                {"mcp": mcp, "pip": pip, "dip": dip},
                pasadas=4,
            )
            kd = dict(base, corr=limpiar(corr))
            kd, kp, score = descenso(med, kd, dict(kp0), "t", MANDOS_PULGAR)
            recetas[nombre] = {"dedos": kd, "pulgar": kp, "score": score}
            print(linea(nombre, med.evaluar(kd, kp)[1], score), flush=True)
        browser.close()

    casos = [("0_catalogo", pose_catalogo())] + [
        (n, construir(r["dedos"], r["pulgar"])) for n, r in recetas.items()
    ]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "_recetas.json").write_text(json.dumps(recetas, indent=2), "utf-8")
    retratar(casos, OUT, cols=5, cell=300)


if __name__ == "__main__":
    main()
