"""S lab 5: pintar encima del render donde cae cada hueso.

En un puno todas las siluetas se parecen y a ojo es imposible decir cual bulto
es el indice y cual el pulgar; en los labs anteriores estuve leyendo mal la
mano. Aqui se proyectan los huesos a pixeles con la matriz de la camara (lo
mismo que hace enfoque_r para recortar) y se dibuja un punto con su nombre
sobre la captura, asi que la lectura deja de ser interpretable.
"""
import time
from pathlib import Path

from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright

from enfoque_r import CAJA_JS
from pose_lab_e import HAND_POS_JS, free_camera
from pose_lab_s import pose_s
import search_e9 as se9
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "mapa_s"
OUT.mkdir(parents=True, exist_ok=True)

se9.URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=s5"

# Proyecta cada hueso pedido a pixeles del visor, uno por uno.
PROY_JS = CAJA_JS.replace(
    "  if (!n) return { error: 'sin-huesos' };\n  return { x0, y0, x1, y1, w: rect.width, h: rect.height };",
    "  return { pts: pts, w: rect.width, h: rect.height };",
).replace(
    "  let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9, n = 0;",
    "  const pts = {};",
).replace(
    """    x0 = Math.min(x0, px); x1 = Math.max(x1, px);
    y0 = Math.min(y0, py); y1 = Math.max(y1, py);
    n++;""",
    "    pts[nombre] = { x: px, y: py, z: clip.z / clip.w };",
)

# De frente (como en produccion), de perfil por el lado del pulgar y desde
# arriba, que es donde se ve si el pulgar cruza por delante o se hunde.
VISTAS = (("frente", 0), ("perfil", -70), ("arriba", None))


def cerca(page, grados):
    """Camara pegada a la mano; sin esto las etiquetas no se leen."""
    h = page.evaluate(HAND_POS_JS)
    orbit = "0deg 40deg 0.85m" if grados is None else f"{grados}deg 84deg 0.85m"
    page.evaluate(
        """(a) => {
            const mv = document.getElementById('handViewer');
            mv.cameraTarget = a.t;
            mv.cameraOrbit = a.orbit;
            mv.fieldOfView = '26deg';
            mv.jumpCameraToGoal();
        }""",
        {"t": "%.3fm %.3fm %.3fm" % (h["x"], h["y"], h["z"]), "orbit": orbit},
    )
    time.sleep(0.22)


ETIQUETAS = {
    "mixamorig1RightHand_035": ("muneca", (255, 255, 255)),
    "mixamorig1RightHandIndex1_040": ("I1", (255, 90, 90)),
    "mixamorig1RightHandIndex2_041": ("I2", (255, 90, 90)),
    "mixamorig1RightHandIndex4_043": ("I4", (255, 90, 90)),
    "mixamorig1RightHandMiddle1_044": ("M1", (255, 200, 60)),
    "mixamorig1RightHandMiddle2_045": ("M2", (255, 200, 60)),
    "mixamorig1RightHandMiddle4_047": ("M4", (255, 200, 60)),
    "mixamorig1RightHandRing1_048": ("R1", (110, 230, 110)),
    "mixamorig1RightHandRing4_051": ("R4", (110, 230, 110)),
    "mixamorig1RightHandPinky1_052": ("P1", (110, 190, 255)),
    "mixamorig1RightHandPinky4_055": ("P4", (110, 190, 255)),
    "mixamorig1RightHandThumb1_036": ("T1", (255, 120, 255)),
    "mixamorig1RightHandThumb2_037": ("T2", (255, 120, 255)),
    "mixamorig1RightHandThumb3_038": ("T3", (255, 120, 255)),
    "mixamorig1RightHandThumb4_039": ("T4", (255, 40, 255)),
}


def anota(page, ruta, escala=2):
    page.evaluate(
        "() => new Promise((r) => requestAnimationFrame("
        "() => requestAnimationFrame(r)))"
    )
    proy = page.evaluate(PROY_JS, list(ETIQUETAS))
    page.query_selector("#handViewer").screenshot(path=str(ruta))

    im = Image.open(ruta).convert("RGB")
    im = im.resize((im.width * escala, im.height * escala), Image.LANCZOS)
    ex = im.width / proy["w"]
    ey = im.height / proy["h"]
    d = ImageDraw.Draw(im)
    for hueso, (txt, color) in ETIQUETAS.items():
        p = proy["pts"].get(hueso)
        if not p:
            continue
        x, y = p["x"] * ex, p["y"] * ey
        d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=color, outline=(0, 0, 0))
        d.text((x + 7, y - 6), txt, fill=color)
    im.save(ruta)
    return proy["pts"]


def main():
    import json

    catalogo = json.loads((ROOT / "data" / "catalogo-lsm.json").read_text("utf-8"))
    por_letra = {s["letra"]: s for s in catalogo["senas"]}

    casos = {
        # la B abre la mano: con los huesos etiquetados encima se ve de una vez
        # si la camara mira la palma o el dorso, que es de lo que depende hacia
        # donde tiene que cruzar el pulgar de la S
        "B": por_letra["B"]["pose"],
        "puno": pose_s(cierre=1.0, tcurl=0.0),
        "S_curl09": pose_s(cierre=0.95, tcurl=0.9),
    }

    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 700, "height": 700})
        time.sleep(0.4)
        free_camera(page)

        for nombre, pose in casos.items():
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
            time.sleep(0.3)
            for vista, grados in VISTAS:
                cerca(page, grados)
                anota(page, OUT / f"{nombre}_{vista}.png")

        browser.close()
    print("Capturas en", OUT)


if __name__ == "__main__":
    main()
