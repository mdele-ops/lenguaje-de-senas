"""P lab 3: elegir el giro de muneca comparando de cerca contra la lamina.

De frente (que es como se ve en practica.html) el medio apunta a la camara y
la P no se lee. Girando la muneca la escuadra indice-medio vuelve a verse, pero
hay dos giros posibles y dan imagenes en espejo:

  wy positivo  el medio cruza hacia el pecho -> se ve el lado del pulgar,
               que es justo el encuadre de la lamina.
  wy negativo  el medio sale hacia afuera -> se ve el dorso, la lamina al reves.

Se recortan las capturas a la mano para poder compararlas con la lamina al
mismo tamaño.
"""
import json
import time
from pathlib import Path

from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright

from pose_lab_e import HAND_POS_JS, free_camera
from pose_lab_p import MEASURE_JS, REF, pose_p
import search_e9 as se9
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "lab_p3"
OUT.mkdir(parents=True, exist_ok=True)

se9.URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=p3"

# Encuadre unico: el de produccion (0deg) pero con teleobjetivo, para que la
# mano llene el cuadro sin meter la camara dentro del brazo del avatar.
ORBIT = "0deg 84deg 1.40m"
FOV = "17deg"

BASE = dict(mid_mcp=90, spread=(4, -4), tcurl=0.15, taside=0.45, t1={"y": -25})

CASES = {
    "wy00": pose_p(**BASE),
    "wy25": pose_p(**BASE, wrist={"y": 25}),
    "wy40": pose_p(**BASE, wrist={"y": 40}),
    "wy55": pose_p(**BASE, wrist={"y": 55}),
    "wy70": pose_p(**BASE, wrist={"y": 70}),
    "wy-35": pose_p(**BASE, wrist={"y": -35}),
    "wy-50": pose_p(**BASE, wrist={"y": -50}),
    "wy-65": pose_p(**BASE, wrist={"y": -65}),
    # con el brazo mas separado del cuerpo la mano no se recorta contra el torso
    "wy55_arm": pose_p(**BASE, wrist={"y": 55}, arm_z=-30),
    "wy55_x12": pose_p(**BASE, wrist={"y": 55, "x": 12}),
    "wy55_z-15": pose_p(**BASE, wrist={"y": 55, "z": -15}),
    "wy55_z15": pose_p(**BASE, wrist={"y": 55, "z": 15}),
}


def hoja_comparativa(items, out_path, cols=4, cell=300):
    lh = 22
    filas = (len(items) + cols - 1) // cols
    canvas = Image.new("RGB", (cols * cell, filas * (cell + lh)), (245, 245, 248))
    draw = ImageDraw.Draw(canvas)
    for i, (name, path) in enumerate(items):
        x, y = (i % cols) * cell, (i // cols) * (cell + lh)
        im = Image.open(path).convert("RGB")
        # cuadrado centrado para que todas las miniaturas tengan la misma escala
        side = min(im.size)
        im = im.crop(
            (
                (im.width - side) // 2,
                (im.height - side) // 2,
                (im.width + side) // 2,
                (im.height + side) // 2,
            )
        )
        canvas.paste(im.resize((cell, cell), Image.LANCZOS), (x, y))
        draw.rectangle([x, y + cell, x + cell, y + cell + lh], fill=(20, 30, 50))
        draw.text((x + 6, y + cell + 6), name, fill=(255, 255, 255))
    canvas.save(out_path)
    print("Hoja:", out_path)


def main():
    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 900, "height": 900})
        time.sleep(0.3)
        viewer = page.query_selector("#viewer")
        free_camera(page)

        items = [("REF lamina", REF)] if REF.exists() else []
        for name, data in CASES.items():
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", data)
            time.sleep(0.3)
            m = page.evaluate(MEASURE_JS)
            print(
                f"{name:12s} idxUp={m['idxUp']:+.2f} midFwd={m['midFwd']:+.2f} "
                f"midSide={m['midSide']:+.2f} ang={m['escuadra']:5.1f} "
                f"tMid={m['thumbMid']:.2f} tY={m['thumbTipY']:+.2f}"
            )
            hand = page.evaluate(HAND_POS_JS)
            page.evaluate(
                """(a) => {
                    const mv = document.getElementById('handViewer');
                    mv.cameraTarget = a.t;
                    mv.cameraOrbit = a.orbit;
                    mv.fieldOfView = a.fov;
                    mv.jumpCameraToGoal();
                }""",
                {
                    "t": "%.3fm %.3fm %.3fm" % (hand["x"], hand["y"], hand["z"]),
                    "orbit": ORBIT,
                    "fov": FOV,
                },
            )
            time.sleep(0.15)
            path = OUT / f"{name}.png"
            viewer.screenshot(path=str(path))
            items.append((name, path))

        browser.close()

    hoja_comparativa(items, OUT / "_comparativa.png", cols=4, cell=320)
    (OUT / "_casos.json").write_text(json.dumps(CASES, indent=2), "utf-8")


if __name__ == "__main__":
    main()
