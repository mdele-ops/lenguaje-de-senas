"""U lab 1: indice y medio juntos hacia arriba, no cruzados ni en V.

La foto de referencia (U_usuario.png) pide:
  - palma de frente
  - indice y medio estirados, pegados uno al otro en toda su longitud
  - anular y menique recogidos
  - pulgar tumbado cruzando por delante de esos dos, no de pie al costado

La U del catalogo solo pone curl 0/0/0.95/0.95: los dos dedos largos quedan
separados (se lee casi como una V suave) y el pulgar no monta sobre el puno.
Este lab parte de la geometria de la R (mismos ejes: z acerca de lado, x
adelanta) pero pide lo CONTRARIO del cruce: las yemas se quedan cada una en
su lado (cruce < 0) y se rozan (sepYemas ~ grosor de un dedo).
"""
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from enfoque_r import MANO, captura, hoja
from pose_lab_e import ARM, BONES, T1, T2, free_camera
from pose_lab_r import MEASURE_JS
from ver_s import CAM_FOV, CAM_ORBIT, CAM_TARGET
import search_e9 as se9
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "lab_u"
OUT.mkdir(parents=True, exist_ok=True)
REF = ROOT / "tools" / "screenshots" / "referencia" / "U_usuario.png"

se9.URL = "http://127.0.0.1:8006/practica.html?letra=%E2%97%8B&v=u1"

# El pulgar de la R/S: tumbado sobre anular y menique, no en escuadra.
PULGAR_R = {T1: {"y": -30, "z": 40}, T2: {"x": 60}}


def pose_u(
    iz=0,
    mz=0,
    ix=0,
    mx=0,
    iz2=0,
    mz2=0,
    tcurl=0.35,
    taside=-0.6,
    thumb=None,
    arm_z=-18,
    cierre=0.95,
    icurl=0.0,
    mcurl=0.0,
):
    """U: dos dedos largos. iz/mz acercan de lado; ix/mx adelantan."""
    ex = {ARM: {"z": arm_z}}
    idx = {}
    med = {}
    if ix or iz:
        idx[0] = {k: v for k, v in (("x", ix), ("z", iz)) if v}
    if mx or mz:
        med[0] = {k: v for k, v in (("x", mx), ("z", mz)) if v}
    if iz2:
        idx[1] = dict(idx.get(1, {}), z=iz2)
    if mz2:
        med[1] = dict(med.get(1, {}), z=mz2)
    for cadena, rots in ((BONES["index"], idx), (BONES["middle"], med)):
        for i, rot in rots.items():
            ex[cadena[i]] = dict(ex.get(cadena[i], {}), **rot)
    for name, rot in (PULGAR_R if thumb is None else thumb).items():
        ex[name] = dict(ex.get(name, {}), **rot)
    return {
        "thumb": {"curl": tcurl, "aside": taside},
        "index": {"curl": icurl},
        "middle": {"curl": mcurl},
        "ring": {"curl": cierre},
        "pinky": {"curl": cierre},
        "extra": ex,
    }


def cam(page, orbit=CAM_ORBIT):
    page.evaluate(
        """(a) => {
            const mv = document.getElementById('handViewer');
            mv.cameraTarget = a.t;
            mv.cameraOrbit = a.orbit;
            mv.fieldOfView = a.fov;
            mv.jumpCameraToGoal();
        }""",
        {"t": CAM_TARGET, "orbit": orbit, "fov": CAM_FOV},
    )
    time.sleep(0.22)


def linea(nombre, m):
    return (
        f"{nombre:22s} cruce={m['cruce']:+5.2f} yemas={m['sepYemas']:.3f} "
        f"gap={m['gap']:.3f} altI={m['altIdx']:+5.2f} altM={m['altMed']:+5.2f} "
        f"thLat={m['thLat']:+5.2f} thH={m['thHoriz']:.2f} puno={m['punoMax']:.2f}"
    )


def main():
    catalogo = json.loads((ROOT / "data" / "catalogo-lsm.json").read_text("utf-8"))
    por = {s["letra"]: s["pose"] for s in catalogo["senas"]}

    casos = {
        "00_U_catalogo": por["U"],
        "01_base_pulgarR": pose_u(),
        # acercar indice (+z hacia menique) y medio (-z hacia indice)
        "02_z6": pose_u(iz=6, mz=-6),
        "03_z10": pose_u(iz=10, mz=-10),
        "04_z14": pose_u(iz=14, mz=-14),
        "05_z18": pose_u(iz=18, mz=-18),
        "06_z10_x8": pose_u(iz=10, mz=-10, ix=8, mx=8),
        "07_V": por["V"],
        "08_R": por["R"],
    }

    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 1000, "height": 1000})
        time.sleep(0.4)
        free_camera(page)

        items = [("REF foto", REF)] if REF.exists() else []
        medidas = {}
        for nombre, pose in casos.items():
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
            time.sleep(0.28)
            m = page.evaluate(MEASURE_JS)
            medidas[nombre] = m
            if m.get("error"):
                print(" ", nombre, m)
                continue
            print(" ", linea(nombre, m))
            cam(page)
            ruta = OUT / f"{nombre}.png"
            captura(page, ruta, MANO, margen=0.28, lado=520)
            items.append((nombre, ruta))

        browser.close()

    hoja(items, OUT / "_hoja.png", cols=3, cell=360, titulo="U · lab 1")
    (OUT / "_medidas.json").write_text(
        json.dumps(medidas, indent=2), encoding="utf-8"
    )
    print("Capturas en", OUT)


if __name__ == "__main__":
    main()
