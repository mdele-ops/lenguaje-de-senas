"""Hoja de contactos de las candidatas de la E.

Cada candidata se ve en la camara real de la app (asi la vera el usuario) y en
un primer plano frontal con los huesos dibujados encima, para poder confirmar
que ningun dedo se atraviesa y que el pulgar queda corto.
"""
import json
import time
from pathlib import Path

from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright

from overlay_e import PROJECT_JS, dibujar_overlay, nombres_huesos
from search_e10 import CAM_PROD_JS, SCREEN_JS, linea, puntuar
from search_e9 import MEASURE_JS, abrir, pose_e

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "cmp_e10"
REF = ROOT / "tools" / "screenshots" / "referencia"

PULGAR_OK = dict(tcurl=0.9, taside=-0.5, t1y=-60, t1z=15, t2x=60, t3x=70)


def catalogo_actual():
    cat = json.loads((ROOT / "data" / "catalogo-lsm.json").read_text("utf-8"))
    return next(s for s in cat["senas"] if s["letra"] == "E")["pose"]


CANDIDATAS = {
    "0_actual": catalogo_actual(),
    "A_85_85_c-4": pose_e(85, 85, 0, -4, **PULGAR_OK),
    "B_85_85_c0": pose_e(85, 85, 0, 0, **PULGAR_OK),
    "C_85_100_d20": pose_e(85, 100, 20, -4, **PULGAR_OK),
    "D_70_100_d25": pose_e(70, 100, 25, -4, **PULGAR_OK),
    "E_100_100": pose_e(100, 100, 0, -4, **PULGAR_OK),
    # variantes de pulgar sobre la mejor forma de dedos
    "F_t3x50": pose_e(85, 85, 0, -4, 0.9, -0.5, -60, 15, 60, 50),
    "G_t3x85": pose_e(85, 85, 0, -4, 0.9, -0.5, -60, 15, 60, 85),
    "H_t2x85": pose_e(85, 85, 0, -4, 0.9, -0.5, -60, 15, 85, 70),
    "I_tc07": pose_e(85, 85, 0, -4, 0.7, -0.5, -60, 15, 60, 70),
}

HAND_TARGET_JS = """
() => {
  const mv = document.getElementById('handViewer');
  let s = null;
  for (const sym of Object.getOwnPropertySymbols(mv)) {
    const v = mv[sym];
    if (v && typeof v.traverse === 'function') { s = v; break; }
    if (v && v.model && typeof v.model.traverse === 'function') { s = v.model; break; }
    if (v && v.target && typeof v.target.traverse === 'function') { s = v.target; break; }
  }
  s.updateMatrixWorld(true);
  const w = {};
  s.traverse((o) => {
    if (o.name === 'mixamorig1RightHand_035' || o.name === 'mixamorig1RightHandMiddle2_045') w[o.name] = o;
  });
  const a = w['mixamorig1RightHand_035'].matrixWorld.elements;
  const b = w['mixamorig1RightHandMiddle2_045'].matrixWorld.elements;
  const off = (s.target && s.target.position) || { x: 0, y: 0, z: 0 };
  return { x: (a[12]+b[12])/2 - off.x, y: (a[13]+b[13])/2 - off.y, z: (a[14]+b[14])/2 - off.z };
}
"""


def recorte(page, viewer, destino, overlay):
    tmp = destino.with_suffix(".full.png")
    page.screenshot(path=str(tmp))
    if overlay:
        res = page.evaluate(PROJECT_JS, nombres_huesos())
        if "error" not in res:
            dibujar_overlay(tmp, res["pts"], tmp)
    box = viewer.bounding_box()
    img = Image.open(tmp)
    x, y = int(box["x"]), int(box["y"])
    w, h = int(box["width"]), int(box["height"])
    lado = min(w, h)
    img.crop((x + (w - lado) // 2, y, x + (w - lado) // 2 + lado, y + lado)).save(destino)
    tmp.unlink()
    return destino


def hoja(items, out_path, cols=4, cell=300):
    lh = 22
    filas = (len(items) + cols - 1) // cols
    c = Image.new("RGB", (cols * cell, filas * (cell + lh)), (245, 245, 248))
    d = ImageDraw.Draw(c)
    for i, (n, p) in enumerate(items):
        x, y = (i % cols) * cell, (i // cols) * (cell + lh)
        c.paste(Image.open(p).convert("RGB").resize((cell, cell), Image.LANCZOS), (x, y))
        d.rectangle([x, y + cell, x + cell, y + cell + lh], fill=(20, 30, 50))
        d.text((x + 6, y + cell + 6), n, fill=(255, 255, 255))
    c.save(out_path)
    print("Hoja:", out_path)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 900, "height": 950})
        time.sleep(0.6)
        viewer = page.query_selector("#viewer")

        app, cerca, lado = [], [], []
        for nombre, pose in CANDIDATAS.items():
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
            time.sleep(0.5)
            page.evaluate(CAM_PROD_JS)
            time.sleep(0.4)
            m = page.evaluate(MEASURE_JS)
            s = page.evaluate(SCREEN_JS)
            print(linea(nombre, m, s, puntuar(m, s)))
            app.append((nombre, recorte(page, viewer, OUT / f"{nombre}_app.png", False)))

            hand = page.evaluate(HAND_TARGET_JS)
            t = "%.3fm %.3fm %.3fm" % (hand["x"], hand["y"], hand["z"])
            for etiqueta, orbit, destino in (
                ("cerca", "0deg 84deg 0.62m", cerca),
                ("lado", "-72deg 84deg 0.62m", lado),
            ):
                for _ in range(2):
                    page.evaluate(
                        """(a) => {
                            const mv = document.getElementById('handViewer');
                            mv.cameraTarget = a.t;
                            mv.cameraOrbit = a.o;
                            mv.fieldOfView = '24deg';
                            mv.jumpCameraToGoal();
                        }""",
                        {"t": t, "o": orbit},
                    )
                    time.sleep(0.3)
                destino.append(
                    (nombre, recorte(page, viewer, OUT / f"{nombre}_{etiqueta}.png", True))
                )
        browser.close()

    ref = [(n, p) for n, p in [("REF foto", REF / "E_usuario.png")] if p.exists()]
    hoja(ref + app, OUT / "_app.png")
    hoja(ref + cerca, OUT / "_cerca.png")
    hoja(ref + lado, OUT / "_lado.png")


if __name__ == "__main__":
    main()
