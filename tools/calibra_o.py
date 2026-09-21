"""Iguala el arco de los cuatro dedos de la O, dedo a dedo.

Mismo problema y misma solucion que en la E (ver calibra_e.py): el reposo del
.glb trae una curvatura distinta horneada en cada dedo, asi que con el mismo
`curl` los angulos no salen iguales. En la O afinada la ultima falange iba de
14 grados en el anular a 41 en el indice, y el arco se veia escalonado.

No se busca en rejilla: se mide el angulo, se le resta al objetivo y la
diferencia se suma al `extra.x` de ese hueso. Cada grado anadido mueve el
angulo casi un grado, asi que tres pasadas convergen.
"""
from pose_lab_e import FINGERS
from pose_o import dedos

MCP, PIP, DIP = 0, 1, 2


def objetivo_medio(o):
    """El arco que ya tiene la pose, pero igual en los cuatro dedos."""
    return {"mcp": o["arco"][MCP], "pip": o["arco"][PIP], "dip": o["arco"][DIP]}


def calibrar(medir, kd, objetivo, pasadas=3):
    """`medir` recibe kwargs de `dedos()` y devuelve las metricas de medida_o."""
    corr = {f: [0.0, 0.0, 0.0] for f in FINGERS}
    o = None
    for _ in range(pasadas):
        o = medir(dict(kd, corr=corr))
        for i, f in enumerate(FINGERS):
            corr[f][MCP] += objetivo["mcp"] - o["mcp"][i]
            corr[f][PIP] += objetivo["pip"] - o["pip"][i]
            corr[f][DIP] += objetivo["dip"] - o["dip"][i]
    return corr, medir(dict(kd, corr=corr))


def limpiar(corr, minimo=1.5):
    """Quita los retoques que no se ven y solo ensucian el catalogo."""
    return {
        f: [round(g, 1) if abs(g) >= minimo else 0.0 for g in valores]
        for f, valores in corr.items()
    }


def pose(kd, corr=None):
    return dedos(**dict(kd, corr=corr))
