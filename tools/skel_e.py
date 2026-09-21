"""Dibuja el esqueleto de la mano (proyecciones 2D) para cada candidata de la E.

Los renders del avatar son ambiguos por el sombreado y la perspectiva; con las
posiciones de los huesos se ve sin dudas si los dedos estan doblados, cuanto se
separan entre si y cuanto sobresale el pulgar.
"""
import json
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from playwright.sync_api import sync_playwright

from pose_lab_e import _GET_SCENE

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "skel_e"
URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=skel"

CADENAS = {
    "pulgar": [
        "mixamorig1RightHand_035",
        "mixamorig1RightHandThumb1_036",
        "mixamorig1RightHandThumb2_037",
        "mixamorig1RightHandThumb3_038",
        "mixamorig1RightHandThumb4_039",
    ],
    "indice": [
        "mixamorig1RightHand_035",
        "mixamorig1RightHandIndex1_040",
        "mixamorig1RightHandIndex2_041",
        "mixamorig1RightHandIndex3_042",
        "mixamorig1RightHandIndex4_043",
    ],
    "medio": [
        "mixamorig1RightHand_035",
        "mixamorig1RightHandMiddle1_044",
        "mixamorig1RightHandMiddle2_045",
        "mixamorig1RightHandMiddle3_046",
        "mixamorig1RightHandMiddle4_047",
    ],
    "anular": [
        "mixamorig1RightHand_035",
        "mixamorig1RightHandRing1_048",
        "mixamorig1RightHandRing2_049",
        "mixamorig1RightHandRing3_050",
        "mixamorig1RightHandRing4_051",
    ],
    "menique": [
        "mixamorig1RightHand_035",
        "mixamorig1RightHandPinky1_052",
        "mixamorig1RightHandPinky2_053",
        "mixamorig1RightHandPinky3_054",
        "mixamorig1RightHandPinky4_055",
    ],
}
COLORES = {
    "pulgar": "#d62728",
    "indice": "#1f77b4",
    "medio": "#2ca02c",
    "anular": "#ff7f0e",
    "menique": "#9467bd",
}

POS_JS = (
    """
(nombres) => {
  const mv = document.getElementById('handViewer');
"""
    + _GET_SCENE
    + """
  const scene = getScene(mv);
  if (scene.updateMatrixWorld) scene.updateMatrixWorld(true);
  const bones = {};
  scene.traverse((o) => { if (o && o.name) bones[o.name] = o; });
  const out = {};
  nombres.forEach((n) => {
    const b = bones[n];
    if (b && b.matrixWorld) {
      const e = b.matrixWorld.elements;
      out[n] = [e[12], e[13], e[14]];
    }
  });
  return out;
}
"""
)


def todos_los_huesos():
    vistos = []
    for cad in CADENAS.values():
        for n in cad:
            if n not in vistos:
                vistos.append(n)
    return vistos


def dibujar(pos, titulo, out_path):
    """Tres proyecciones: palma (x-y), perfil (z-y) y planta (x-z)."""
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.6))
    planos = [
        ("palma  (mirando de frente)", 0, 1, True, False),
        ("perfil (desde el meñique)", 2, 1, False, False),
        ("planta (desde arriba)", 0, 2, True, True),
    ]
    for ax, (nombre, ia, ib, inv_a, inv_b) in zip(axes, planos):
        for dedo, cadena in CADENAS.items():
            pts = [pos[n] for n in cadena if n in pos]
            xs = [p[ia] for p in pts]
            ys = [p[ib] for p in pts]
            ax.plot(xs, ys, "-o", ms=4, lw=2, color=COLORES[dedo], label=dedo)
            ax.annotate(
                dedo[:3], (xs[-1], ys[-1]), fontsize=8, color=COLORES[dedo]
            )
        ax.set_title(nombre, fontsize=9)
        ax.set_aspect("equal")
        ax.grid(alpha=0.25)
        if inv_a:
            ax.invert_xaxis()
        if inv_b:
            ax.invert_yaxis()
    axes[0].legend(fontsize=7, loc="best")
    fig.suptitle(titulo, fontsize=11)
    fig.tight_layout()
    fig.savefig(out_path, dpi=110)
    plt.close(fig)


def capturar(page, poses):
    huesos = todos_los_huesos()
    datos = {}
    for nombre, pose in poses.items():
        page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
        time.sleep(0.35)
        datos[nombre] = page.evaluate(POS_JS, huesos)
    return datos


def abrir(p):
    browser = p.chromium.launch(
        channel="chrome",
        args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"],
    )
    page = browser.new_page(viewport={"width": 700, "height": 700})
    page.goto(URL, wait_until="networkidle", timeout=60000)
    page.wait_for_selector("#anim-info", timeout=20000, state="attached")
    for _ in range(120):
        if page.evaluate(
            "() => !!(window.__LSM_CONTROLLER__ && window.__LSM_CONTROLLER__.isModelReady())"
        ):
            break
        time.sleep(0.4)
    time.sleep(1.5)
    return browser, page


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    catalogo = json.loads((ROOT / "data" / "catalogo-lsm.json").read_text("utf-8"))
    pose_catalogo = next(s for s in catalogo["senas"] if s["letra"] == "E")["pose"]

    poses = {"E_catalogo": pose_catalogo}
    with sync_playwright() as p:
        browser, page = abrir(p)
        datos = capturar(page, poses)
        browser.close()

    for nombre, pos in datos.items():
        dibujar(pos, nombre, OUT / f"{nombre}.png")
        print("->", OUT / f"{nombre}.png")


if __name__ == "__main__":
    main()
