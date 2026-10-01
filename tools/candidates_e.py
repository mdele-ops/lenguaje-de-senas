"""Candidatas de la letra E que se comparan contra la referencia.

Solo datos: `compare_e.py` las aplica y arma la hoja. El reparto es
MCP poco / PIP mucho (nudillos arriba, yemas abajo) + pulgar atravesado.
"""
from pose_lab_e import ARM, BONES, FINGERS, T1, T2, T3

FAN = (-1.5, -0.5, 0.5, 1.5)


def _four(v):
    return v if isinstance(v, (tuple, list)) else (v,) * 4


def pose_e(
    mcp=70,
    pip=92,
    dip=0,
    conv=12,
    tcurl=0.6,
    taside=-0.5,
    t1=(-60, 0),
    t2x=60,
    t3x=0,
    arm_z=-18,
    wrist=None,
):
    """mcp/pip/dip aceptan un valor o una tupla (index, middle, ring, pinky)."""
    mcp, pip, dip = _four(mcp), _four(pip), _four(dip)
    extra = {ARM: {"z": arm_z}, T1: {"y": t1[0], "z": t1[1]}}
    for i, f in enumerate(FINGERS):
        b = BONES[f]
        extra[b[0]] = {"x": mcp[i]}
        extra[b[1]] = {"x": pip[i]}
        if dip[i]:
            extra[b[2]] = {"x": dip[i]}
    if t2x:
        extra[T2] = {"x": t2x}
    if t3x:
        extra[T3] = {"x": t3x}
    pose = {"thumb": {"curl": tcurl, "aside": taside}, "extra": extra}
    for i, f in enumerate(FINGERS):
        pose[f] = {"curl": 0.0, "spread": FAN[i] * conv}
    if wrist:
        pose["muneca"] = dict(wrist)
    return pose


CANDIDATES = {
    "a_actual": {
        "thumb": {"curl": 0.6},
        "index": {"curl": 0.9},
        "middle": {"curl": 0.9},
        "ring": {"curl": 0.9},
        "pinky": {"curl": 0.9},
    },
    # Pulido final: que el dedo medio no sobresalga por delante del pulgar y que
    # el hueco anular-menique se cierre.
    "b_catalogo": pose_e(conv=18, dip=25, pip=(86, 80, 82, 86), t1=(-60, 10)),
    "c_medio84": pose_e(conv=18, dip=25, pip=(86, 84, 84, 88), t1=(-60, 10)),
    "d_medio88": pose_e(conv=18, dip=25, pip=(86, 88, 86, 90), t1=(-60, 10)),
    "e_medio84_conv22": pose_e(conv=22, dip=25, pip=(86, 84, 84, 88), t1=(-60, 10)),
    "f_medio84_dip30": pose_e(conv=18, dip=30, pip=(86, 84, 84, 88), t1=(-60, 10)),
    "g_medio84_z16": pose_e(conv=18, dip=25, pip=(86, 84, 84, 88), t1=(-60, 16)),
    "h_menique": pose_e(
        conv=18, dip=25, mcp=(70, 70, 70, 76), pip=(86, 84, 84, 90), t1=(-60, 10)
    ),
}
