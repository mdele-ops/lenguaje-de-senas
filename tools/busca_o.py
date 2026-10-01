"""Busqueda de la O: se barren dedos y pulgar por separado y se cruzan.

El truco esta en que el marco de la palma (muneca + fila de nudillos) no se
mueve al doblar los dedos ni el pulgar. Midiendo las dos familias por separado
en ese marco, las N*M combinaciones salen de N+M renderizados en vez de N*M:
180 + 512 medidas dan 92160 candidatas en poco mas de un minuto.

Lo que se busca es lo que separa la O de la C: que el aro CIERRE (yema del
pulgar contra yema del indice) sin que el agujero se pierda.
"""
import itertools
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from medida_o import HUESOS, MARCO_JS, detalle, linea, metricas, puntuar
from pose_o import dedos, pulgar
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "busca_o.json"

DEDO_BONES = tuple(n.split("_")[0] for n in HUESOS if not n.startswith("Thumb"))
PULGAR_BONES = tuple(n.split("_")[0] for n in HUESOS if n.startswith("Thumb"))

REJILLA_DEDOS = {
    "curl": (0.52, 0.60, 0.68, 0.76, 0.84),
    "mcp": (-8, 0, 8, 16),
    "dip": (-18, -8, 2),
    "fan": (0, 6, 12),
}

REJILLA_PULGAR = {
    "curl": (0.35, 0.50, 0.65, 0.80),
    "aside": (0.2, 0.5, 0.8, 1.1),
    "t1y": (5, 20, 35, 50),
    "t1z": (-10, 5, 20, 35),
    "t2x": (0, 20),
    "t3x": (0, 25),
}


def combinaciones(rejilla):
    claves = list(rejilla)
    for valores in itertools.product(*(rejilla[k] for k in claves)):
        yield dict(zip(claves, valores))


def barrer(page, rejilla, construir, huesos, etiqueta):
    salida = []
    total = 1
    for v in rejilla.values():
        total *= len(v)
    t0 = time.time()
    for i, kw in enumerate(combinaciones(rejilla)):
        page.evaluate(
            "(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", construir(**kw)
        )
        marco = page.evaluate(MARCO_JS)
        if "error" in marco:
            raise RuntimeError(marco["error"])
        salida.append((kw, {h: marco[h] for h in huesos}))
        if (i + 1) % 50 == 0 or i + 1 == total:
            print(f"  {etiqueta} {i+1}/{total}  ({time.time()-t0:.0f}s)", flush=True)
    return salida


def dedos_kw(curl, mcp, dip, fan):
    return dedos(curl, mcp=mcp, dip=dip, fan=fan)


def pulgar_kw(curl, aside, t1y, t1z, t2x, t3x):
    return pulgar(curl, aside, t1={"y": t1y, "z": t1z}, t2x=t2x, t3x=t3x)


def main():
    with sync_playwright() as p:
        browser, page = abrir(p)
        print("barriendo dedos...", flush=True)
        dd = barrer(page, REJILLA_DEDOS, dedos_kw, DEDO_BONES, "dedos")
        print("barriendo pulgar...", flush=True)
        pp = barrer(page, REJILLA_PULGAR, pulgar_kw, PULGAR_BONES, "pulgar")
        browser.close()

    print(f"cruzando {len(dd)} x {len(pp)} = {len(dd)*len(pp)}...", flush=True)
    ranking = []
    for kd, md in dd:
        for kp, mp in pp:
            o = metricas({**md, **mp})
            ranking.append((puntuar(o), kd, kp, o))
    ranking.sort(key=lambda r: r[0])

    print("\n--- mejores 15 ---")
    for score, kd, kp, o in ranking[:15]:
        print(linea("", o, score))
        print("      dedos", kd, " pulgar", kp)
    print()
    print(detalle(ranking[0][3]))

    OUT.write_text(
        json.dumps(
            [
                {"score": s, "dedos": kd, "pulgar": kp, "medidas": o}
                for s, kd, kp, o in ranking[:60]
            ],
            indent=2,
        ),
        "utf-8",
    )
    print("\n->", OUT)


if __name__ == "__main__":
    main()
