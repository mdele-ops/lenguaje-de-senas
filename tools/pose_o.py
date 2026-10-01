"""Como se arma la pose de la O, en dos piezas independientes.

Los cuatro dedos y el pulgar se controlan con huesos distintos, asi que se
pueden probar por separado y juntar despues (ver medida_o.metricas). Este
modulo solo construye los diccionarios de pose.

    dedos()   el arco: los cuatro dedos doblados por igual y juntos, con un
              retoque por falange para repartir la curva (el `curl` solo
              reparte en la proporcion fija del rig, 72/90/68).
    pulgar()  el pulgar opuesto, que sube a buscar las yemas. `curl`/`aside`
              no bastan para orientarlo: hace falta girar la base (Thumb1),
              igual que en la E.
"""
from pose_lab_e import ARM, BONES, FINGERS, T1, T2, T3

# Abanico: negativo acerca el dedo al indice. Con el mismo `fan` para los
# cuatro, los dedos se juntan en bloque sin cruzarse.
ABANICO = (-1.0, -1 / 3, 1 / 3, 1.0)


def dedos(curl, mcp=0, pip=0, dip=0, fan=0, corr=None):
    """`corr` es {dedo: [mcp, pip, dip]} en grados, encima del retoque comun.

    Hace falta porque el reposo del .glb no es simetrico: con el mismo `curl`
    en los cuatro dedos la ultima falange del anular se queda a 14 grados y la
    del indice llega a 41, y el arco de la O sale escalonado.
    """
    pose = {}
    extra = {}
    for i, f in enumerate(FINGERS):
        b = BONES[f]
        c = (corr or {}).get(f, (0, 0, 0))
        for j, base in enumerate((mcp, pip, dip)):
            g = round(base + c[j], 1)
            if g:
                extra[b[j]] = {"x": g}
        pose[f] = {"curl": curl}
        if fan:
            pose[f]["spread"] = round(fan * ABANICO[i], 1)
    if extra:
        pose["extra"] = extra
    return pose


def pulgar(curl, aside, t1=None, t2x=0, t3x=0):
    extra = {}
    if t1:
        extra[T1] = {k: v for k, v in t1.items() if v}
    if t2x:
        extra[T2] = {"x": t2x}
    if t3x:
        extra[T3] = {"x": t3x}
    pose = {"thumb": {"curl": curl, "aside": aside}}
    if extra:
        pose["extra"] = extra
    return pose


def juntar(*partes, muneca=None, arm_z=None):
    """Funde poses parciales. El `extra` se acumula hueso a hueso."""
    out = {}
    extra = {}
    for parte in partes:
        for clave, val in (parte or {}).items():
            if clave == "extra":
                for hueso, rot in val.items():
                    extra[hueso] = dict(extra.get(hueso, {}), **rot)
            else:
                out[clave] = dict(out.get(clave, {}), **val)
    if arm_z:
        extra[ARM] = dict(extra.get(ARM, {}), z=arm_z)
    if muneca:
        out["muneca"] = dict(muneca)
    if extra:
        out["extra"] = extra
    return out
