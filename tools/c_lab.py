"""Banco de pruebas de la letra C: construye poses, mide y fotografia.

Se importa desde los scripts c_stageN.py para no repetir codigo.
"""
import json
from pathlib import Path

import lab

ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / "tools" / "screenshots"

ARM = "mixamorig1RightArm_033"
FORE = "mixamorig1RightForeArm_034"
T1 = "mixamorig1RightHandThumb1_036"
T2 = "mixamorig1RightHandThumb2_037"
T3 = "mixamorig1RightHandThumb3_038"
I1, I2 = "mixamorig1RightHandIndex1_040", "mixamorig1RightHandIndex2_041"
M1, M2 = "mixamorig1RightHandMiddle1_044", "mixamorig1RightHandMiddle2_045"
R1, R2 = "mixamorig1RightHandRing1_048", "mixamorig1RightHandRing2_049"
P1, P2 = "mixamorig1RightHandPinky1_052", "mixamorig1RightHandPinky2_053"

I3 = "mixamorig1RightHandIndex3_042"
M3 = "mixamorig1RightHandMiddle3_046"
R3 = "mixamorig1RightHandRing3_050"
P3 = "mixamorig1RightHandPinky3_054"

KNUCKLES = (I1, M1, R1, P1)
MIDS = (I2, M2, R2, P2)
DISTS = (I3, M3, R3, P3)

# Separacion leve entre dedos: en la foto los cuatro van juntos, en un solo arco.
SPREAD = (8, 3, -3, -8)


def build(
    curl=0.30,
    knuckle=34,
    mid=20,
    dist=0,
    tcurl=0.28,
    taside=0.45,
    thumb=None,
    wy=90,
    wz=-15,
    wx=0,
    arm_z=-18,
    arm=None,
    spread=SPREAD,
):
    """Pose de C parametrizada.

    curl/knuckle/mid/dist -> arco de los cuatro dedos: curl global mas extra en
                             nudillo (MCP), falange media (PIP) y distal (DIP)
    tcurl/taside/thumb    -> pulgar opuesto que cierra el arco por abajo
    wx/wy/wz              -> giro de la muneca (wy pone la palma de perfil)
    """
    extra = {}
    for bone in KNUCKLES:
        extra[bone] = {"x": knuckle}
    if mid:
        for bone in MIDS:
            extra[bone] = {"x": mid}
    if dist:
        for bone in DISTS:
            extra[bone] = {"x": dist}
    for bone, rot in (thumb if thumb is not None else {T1: {"y": 34, "z": 8}}).items():
        extra[bone] = dict(rot)
    if arm is not None:
        if arm:
            extra[ARM] = dict(arm)
    elif arm_z:
        extra[ARM] = {"z": arm_z}

    muneca = {}
    if wx:
        muneca["x"] = wx
    if wy:
        muneca["y"] = wy
    if wz:
        muneca["z"] = wz

    pose = {
        "thumb": {"curl": tcurl, "aside": taside},
        "index": {"curl": curl, "spread": spread[0]},
        "middle": {"curl": curl, "spread": spread[1]},
        "ring": {"curl": curl, "spread": spread[2]},
        "pinky": {"curl": curl, "spread": spread[3]},
    }
    if muneca:
        pose["muneca"] = muneca
    pose["extra"] = extra
    return pose


FLAT = {
    "thumb": {"curl": 0.0},
    "index": {"curl": 0.0},
    "middle": {"curl": 0.0},
    "ring": {"curl": 0.0},
    "pinky": {"curl": 0.0},
    "extra": {ARM: {"z": -18}},
}

# Objetivos leidos de la foto de referencia, normalizados por el largo del dedo
# extendido: hueco claro entre puntas y dedos curvados sin llegar a cerrar la O.
TARGET_ABERTURA = 0.65
TARGET_CUERDA = 0.80


def launch(p):
    """Chrome del sistema si esta disponible; el chromium de playwright si no.

    El cache de navegadores de playwright vive en un temporal que se limpia solo,
    asi que el canal "chrome" es el camino estable en esta maquina.
    """
    try:
        return p.chromium.launch(channel="chrome", args=lab.CHROME_ARGS)
    except Exception:
        return p.chromium.launch(args=lab.CHROME_ARGS)


def dot(a, b):
    return sum(a[i] * b[i] for i in range(3))


def scales(page):
    """Largo del dedo indice y del pulgar con la mano extendida (unidad de medida)."""
    lab.apply_pose(page, FLAT)
    v = lab.vectors(page, side="right")
    return {
        "dedo": lab.length(lab.sub(v["index1"], v["indexTip"])) or 1e-9,
        "pulgar": lab.length(lab.sub(v["thumb1"], v["thumbTip"])) or 1e-9,
    }


def metrics(page, unit):
    """Orientacion y forma del arco, en el espacio del visor.

    A orbita 0deg la camara mira por -Z, con +X a la derecha de la pantalla y +Y
    arriba. Para que el arco se lea de frente la normal de la palma debe quedar
    horizontal (|palma . X| ~ 1) y el eje indice->menique apuntar a la camara.
    """
    v = lab.vectors(page, side="right")
    o = lab.orientation(v, side="right")
    across = lab.norm(lab.sub(v["pinky1"], v["index1"]))
    d = unit["dedo"]

    return {
        "palma_x": round(dot(o["palma"], [1, 0, 0]), 3),
        "palma_z": round(dot(o["palma"], [0, 0, 1]), 3),
        "dedos_y": round(dot(o["dedos"], [0, 1, 0]), 3),
        "across_z": round(dot(across, [0, 0, 1]), 3),
        # hueco de la C: punta del pulgar a punta del indice
        "abertura": round(lab.length(lab.sub(v["thumbTip"], v["indexTip"])) / d, 3),
        # cuerda del indice: 1.0 = recto, mas chico = mas curvado
        "cuerda": round(lab.length(lab.sub(v["index1"], v["indexTip"])) / d, 3),
        # la punta del indice debe quedar arriba de la del pulgar
        "dy": round((v["indexTip"][1] - v["thumbTip"][1]) / d, 3),
        # dispersion de las cuatro puntas: chico = cuatro dedos en un solo arco
        "juntos": round(lab.length(lab.sub(v["indexTip"], v["pinkyTip"])) / d, 3),
        # el hueco debe abrirse hacia la camara, no hacia adentro
        "hueco_x": round((v["indexTip"][0] - v["thumbTip"][0]) / d, 3),
    }


def score(m):
    """Menor es mejor. Pondera hueco, curvatura, dedos juntos y arco de frente."""
    return (
        abs(m["abertura"] - TARGET_ABERTURA) * 2.4
        + abs(m["cuerda"] - TARGET_CUERDA) * 2.0
        + m["juntos"] * 1.0
        + (1 - abs(m["palma_x"])) * 1.5
        + max(0.0, 0.45 - m["dy"]) * 1.6
    )


def measure_all(cases, verbose=True):
    """Solo mide (sin screenshots): rapido para barrer cientos de combinaciones."""
    from playwright.sync_api import sync_playwright

    catalog = lab.load_catalog()
    rows = []
    with sync_playwright() as p:
        browser = launch(p)
        page = lab.open_lab(browser, catalog)
        unit = scales(page)
        if verbose:
            print("unidad: dedo=%.4f pulgar=%.4f" % (unit["dedo"], unit["pulgar"]))
        for case, pose in cases.items():
            lab.apply_pose(page, pose)
            m = metrics(page, unit)
            m["caso"] = case
            m["score"] = round(score(m), 4)
            rows.append(m)
        browser.close()
    rows.sort(key=lambda r: r["score"])
    return rows


def run(name, cases, orbits=(0,), cols=4, cell=280, radius=None):
    """Aplica cada pose, mide y fotografia. Devuelve la lista de metricas ordenada."""
    from playwright.sync_api import sync_playwright

    out_dir = SHOTS / name
    out_dir.mkdir(parents=True, exist_ok=True)
    catalog = lab.load_catalog()
    rad = radius or lab.RADIUS
    rows = []

    with sync_playwright() as p:
        browser = launch(p)
        page = lab.open_lab(browser, catalog)
        unit = scales(page)
        shots = []
        for case, pose in cases.items():
            lab.apply_pose(page, pose)
            m = metrics(page, unit)
            m["caso"] = case
            m["score"] = round(score(m), 4)
            rows.append(m)
            for deg in orbits:
                suffix = "" if len(orbits) == 1 else f"_{deg:+04d}"
                out = out_dir / f"{case}{suffix}.png"
                lab.shot(page, out, orbit=f"{deg}deg 84deg {rad}", side="right")
                shots.append((f"{case}{suffix}", out))
            print("  ", case, m, flush=True)
        lab.sheet(shots, out_dir / "_hoja.png", cols=cols, cell=cell)
        browser.close()

    (out_dir / "metricas.json").write_text(
        json.dumps({"casos": cases, "metricas": rows}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return rows
