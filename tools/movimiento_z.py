"""Z: keyframes del trazo en el plano de la pantalla.

eje_z.py midio que, con el indice senalando, dos ejes del antebrazo mueven
la yema casi sin mezclarse:

    ForeArm.z -> horizontal (z negativo va a la derecha del espectador)
    ForeArm.x -> vertical   (x positivo baja)

Se resuelven las cuatro esquinas de una Z del tamano de la mano (~84 px)
y se comprueba el camino real de la yema en el visor.
"""
import json
import math
import time
from pathlib import Path

from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright

from enfoque_r import CAJA_JS
from pose_lab_e import ARM, free_camera
from pose_lab_x2 import FOREARM
from pose_lab_z import aplicar, cam, pose_z, abrir
import search_e9 as se9

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "lab_z_mov"
OUT.mkdir(parents=True, exist_ok=True)
JAC = ROOT / "tools" / "screenshots" / "eje_z" / "_jac.json"

se9.URL = "http://127.0.0.1:8006/practica.html?letra=%E2%97%8B&v=zmov2"

ARM_Z = -18
HALF = 42.0  # px a cada lado del centro: Z de ~84 px, un largo de mano
TIP = ["mixamorig1RightHandIndex4_043"]
WRIST = {"x": 0, "y": 0, "z": 0}


def grados(jac, dpx, dpy):
    fx = jac["mixamorig1RightForeArm_034.x"]
    fz = jac["mixamorig1RightForeArm_034.z"]
    a, b = fx["dpx"], fz["dpx"]
    c, d = fx["dpy"], fz["dpy"]
    det = a * d - b * c
    gx = (d * dpx - b * dpy) / det
    gz = (-c * dpx + a * dpy) / det
    return gx, gz


def esquinas(half=HALF):
    return [
        ("TL", -half, -half),
        ("TR", +half, -half),
        ("BL", -half, +half),
        ("BR", +half, +half),
    ]


def tiempos():
    w = 2 * HALF
    diag = math.hypot(w, w)
    total = w + diag + w
    return [0.0, w / total, (w + diag) / total, 1.0]


def keyframes(jac):
    kfs = []
    for (nombre, dpx, dpy), t in zip(esquinas(), tiempos()):
        gx, gz = grados(jac, dpx, dpy)
        kfs.append(
            {
                "nombre": nombre,
                "t": round(t, 4),
                "muneca": dict(WRIST),
                "extra": {
                    ARM: {"z": ARM_Z},
                    FOREARM: {"x": round(gx, 2), "z": round(gz, 2)},
                },
            }
        )
    return kfs


def pose_en(kf):
    pose = pose_z(arm_z=ARM_Z)
    pose["muneca"] = dict(kf["muneca"])
    pose["extra"][ARM] = dict(kf["extra"][ARM])
    pose["extra"][FOREARM] = dict(kf["extra"][FOREARM])
    return pose


def catalog_kfs(kfs):
    return [
        {
            "t": kf["t"],
            "muneca": dict(kf["muneca"]),
            "extra": {
                ARM: dict(kf["extra"][ARM]),
                FOREARM: dict(kf["extra"][FOREARM]),
            },
        }
        for kf in kfs
    ]


def punta(page):
    caja = page.evaluate(CAJA_JS, TIP)
    return {
        "x": (caja["x0"] + caja["x1"]) / 2,
        "y": (caja["y0"] + caja["y1"]) / 2,
    }


def main():
    jac = json.loads(JAC.read_text(encoding="utf-8"))["jac"]
    kfs = keyframes(jac)
    print("keyframes:")
    for kf in kfs:
        fa = kf["extra"][FOREARM]
        print(f"  {kf['nombre']} t={kf['t']:.3f}  ForeArm x={fa['x']:+6.2f} z={fa['z']:+6.2f}")

    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 1100, "height": 900})
        time.sleep(0.3)
        viewer = page.query_selector("#viewer")
        free_camera(page)
        cam(page)

        puntos = []
        for kf in kfs:
            aplicar(page, pose_en(kf))
            cam(page)
            m = punta(page)
            puntos.append((m["x"], m["y"]))
            print(f"  {kf['nombre']} pantalla=({m['x']:.1f},{m['y']:.1f})")
            viewer.screenshot(path=str(OUT / f"{kf['nombre']}_prod.png"))
            time.sleep(0.1)

        # hoja de produccion con el trazo pintado encima del primer cuadro
        base = Image.open(OUT / "TL_prod.png").convert("RGB")
        draw = ImageDraw.Draw(base)
        # las coords de CAJA_JS son del <model-viewer>, no de #viewer
        visor = page.evaluate(
            """() => {
                const mv = document.getElementById('handViewer');
                const v = document.getElementById('viewer');
                const a = mv.getBoundingClientRect();
                const b = v.getBoundingClientRect();
                return { dx: a.left - b.left, dy: a.top - b.top };
            }"""
        )
        pts = [(x + visor["dx"], y + visor["dy"]) for x, y in puntos]
        draw.line(pts, fill=(128, 32, 48), width=4)
        for i, (px, py) in enumerate(pts):
            draw.ellipse((px - 5, py - 5, px + 5, py + 5), fill=(128, 32, 48))
            draw.text((px + 8, py - 10), kfs[i]["nombre"], fill=(255, 220, 220))
        base.save(OUT / "_trazo_prod.png")

        browser.close()

    xs = [q[0] for q in puntos]
    ys = [q[1] for q in puntos]
    print(
        f"ancho={max(xs)-min(xs):.1f}px alto={max(ys)-min(ys):.1f}px "
        f"(objetivo {2*HALF:.0f} x {2*HALF:.0f})"
    )
    (OUT / "_keyframes.json").write_text(
        json.dumps({"ciclo": catalog_kfs(kfs), "puntos": puntos}, indent=2),
        encoding="utf-8",
    )
    print("->", OUT)


if __name__ == "__main__":
    main()
