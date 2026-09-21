"""Iguala el doblez de los cuatro dedos resolviendo una correccion por hueso.

El problema: `curl` reparte los grados por igual entre los cuatro dedos, pero
el reposo del modelo no es simetrico (cada dedo trae su propia curvatura
horneada en el .glb). Con `curl: 0.92` en los cuatro salen angulos distintos
por dedo, sobre todo en la ultima falange:

    dip = [69.9  58.9  42.9  67.2]   -> 27 grados de diferencia

y en pantalla eso es una fila de yemas escalonada.

Aqui no se busca en una rejilla: se mide, se compara con el angulo objetivo y
se corrige. Cada grado que se anade al `extra.x` de un hueso mueve su angulo
casi un grado, asi que dos o tres pasadas de punto fijo convergen.
"""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

from pose_lab_e import ARM, BONES, FINGERS, T1, T2, T3
from search_e9 import abrir
from simetria_e import SIMETRIA_JS, detalle, informe

ROOT = Path(__file__).resolve().parents[1]

# posicion en BONES[dedo] de cada articulacion que rota
PROX, MIDD, DIST = 0, 1, 2

# Objetivo de la E, dentro de las bandas anatomicas de search_e11
# (MCP 15-42, PIP 85-112, DIP 50-85). Iguales para los cuatro dedos.
OBJETIVO = {"mcp": 32.0, "pip": 96.0, "dip": 62.0}

# pulgar recogido junto al indice (el ganador de refine_e14)
PULGAR = {
    "curl": 0.95,
    "aside": -0.6,
    T1: {"x": -50, "z": -30},
    T3: {"x": 75},
}

FAN = (-1.5, -0.5, 0.5, 1.5)


def pulgar(curl, aside, t1=None, t2=None, t3=None):
    """Empaqueta los parametros del pulgar en el formato que espera `pose`."""
    p = {"curl": curl, "aside": aside}
    for hueso, rot in ((T1, t1), (T2, t2), (T3, t3)):
        rot = {k: v for k, v in (rot or {}).items() if v}
        if rot:
            p[hueso] = rot
    return p


def pose(curl, conv, correcciones=None, thumb=None, arm_z=-18):
    """E como puno abierto, con una correccion en grados por hueso encima.

    `correcciones` es {dedo: [prox, midd, dist]} en grados; se suma al `extra.x`
    de cada falange despues del curl. `thumb` es lo que devuelve `pulgar()`.
    """
    p = dict(PULGAR if thumb is None else thumb)
    extra = {ARM: {"z": arm_z}}
    for hueso in (T1, T2, T3):
        if p.get(hueso):
            extra[hueso] = dict(p[hueso])

    out = {"thumb": {"curl": p["curl"], "aside": p["aside"]}, "extra": extra}
    for i, f in enumerate(FINGERS):
        out[f] = {"curl": curl, "spread": FAN[i] * conv}
        for j, grados in enumerate((correcciones or {}).get(f, (0, 0, 0))):
            if round(grados, 1):
                extra[BONES[f][j]] = {"x": round(grados, 1)}
    return out


def calibrar(ev, curl, conv, objetivo=OBJETIVO, pasadas=4, verbose=True, thumb=None):
    """Punto fijo: corrige cada hueso por su error de angulo hasta converger."""
    corr = {f: [0.0, 0.0, 0.0] for f in FINGERS}
    s = None
    for n in range(pasadas):
        s = ev(pose(curl, conv, corr, thumb))
        for i, f in enumerate(FINGERS):
            corr[f][PROX] += objetivo["mcp"] - s["mcpAng"][i]
            corr[f][MIDD] += objetivo["pip"] - s["pipAng"][i]
            corr[f][DIST] += objetivo["dip"] - s["dipAng"][i]
        if verbose:
            print(f"  pasada {n + 1}: {informe('', s)}")
    s = ev(pose(curl, conv, corr, thumb))
    return corr, s


def main():
    cat = json.loads((ROOT / "data" / "catalogo-lsm.json").read_text("utf-8"))
    actual = next(x for x in cat["senas"] if x["letra"] == "E")["pose"]

    with sync_playwright() as p:
        browser, page = abrir(p)

        def ev(pz):
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pz)
            return page.evaluate(SIMETRIA_JS)

        s0 = ev(actual)
        print("ACTUAL", informe("E_catalogo", s0))
        print(detalle(s0), "\n")

        print("CALIBRANDO curl=0.0 conv=-4 (todo el doblez sale de la correccion)")
        corr, s = calibrar(ev, 0.0, -4)
        print("FINAL ", informe("E_calibrada", s))
        print(detalle(s))
        print("correcciones:")
        for f in FINGERS:
            print(f"  {f:7s} {[round(v, 1) for v in corr[f]]}")
        browser.close()

    salida = ROOT / "tools" / "screenshots" / "calibra_e.json"
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text(
        json.dumps({"objetivo": OBJETIVO, "correcciones": corr, "medidas": s}, indent=2),
        "utf-8",
    )
    print("\n->", salida)


if __name__ == "__main__":
    main()
