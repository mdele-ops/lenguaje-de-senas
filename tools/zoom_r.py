"""R lab 5: primer plano de SOLO los dos dedos, que es donde esta la letra.

Los encuadres de los otros labs cogen la mano entera y a esa escala el cruce
del indice y el medio cabe en veinte pixeles: no se distingue si los dedos se
cruzan, se tocan o se tapan uno al otro. Aqui la camara se pega a la horquilla
que forman los dos dedos y se gira alrededor para ver el cruce desde varios
lados.
"""
import json
import sys
import time
from pathlib import Path

from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright

from eje_r import cam
from pose_lab_e import _GET_SCENE, free_camera
from pose_lab_r import MEASURE_JS
from search_r import cruzar, puntuar
import search_e9 as se9
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "zoom_r"
OUT.mkdir(parents=True, exist_ok=True)
REF = ROOT / "tools" / "screenshots" / "ref_R_dedos.png"

se9.URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=r5"

# Centro y tamano de los dos dedos extendidos, para pegar la camara justo ahi.
DEDOS_JS = (
    """
() => {
  const mv = document.getElementById('handViewer');
"""
    + _GET_SCENE
    + """
  const scene = getScene(mv);
  scene.updateMatrixWorld(true);
  const B = {};
  scene.traverse((o) => { if (o && o.name) B[o.name] = o; });
  const P = (n) => {
    const b = B[n];
    const e = b.matrixWorld.elements;
    return { x: e[12], y: e[13], z: e[14] };
  };
  const pts = [
    'mixamorig1RightHandIndex1_040', 'mixamorig1RightHandIndex4_043',
    'mixamorig1RightHandMiddle1_044', 'mixamorig1RightHandMiddle4_047',
  ].map(P);
  let c = { x: 0, y: 0, z: 0 };
  pts.forEach((p) => { c.x += p.x/pts.length; c.y += p.y/pts.length; c.z += p.z/pts.length; });
  let r = 0;
  pts.forEach((p) => {
    r = Math.max(r, Math.hypot(p.x-c.x, p.y-c.y, p.z-c.z));
  });
  const off = (scene.target && scene.target.position) || { x: 0, y: 0, z: 0 };
  return { x: c.x - off.x, y: c.y - off.y, z: c.z - off.z, r: r };
}
"""
)

VISTAS = {"frente": 0, "izq": -35, "der": 35, "lado": -80}


def hoja(items, out_path, cols, cell=360):
    lh = 26
    filas = (len(items) + cols - 1) // cols
    canvas = Image.new("RGB", (cols * cell, filas * (cell + lh)), (245, 245, 248))
    draw = ImageDraw.Draw(canvas)
    for i, (name, path) in enumerate(items):
        x, y = (i % cols) * cell, (i // cols) * (cell + lh)
        im = Image.open(path).convert("RGB")
        lado = min(im.size)
        im = im.crop(
            (
                (im.width - lado) // 2,
                (im.height - lado) // 2,
                (im.width + lado) // 2,
                (im.height + lado) // 2,
            )
        )
        canvas.paste(im.resize((cell, cell), Image.LANCZOS), (x, y))
        draw.rectangle([x, y + cell, x + cell, y + cell + lh], fill=(20, 30, 50))
        draw.text((x + 6, y + cell + 8), name, fill=(255, 255, 255))
    canvas.save(out_path)
    print("Hoja:", out_path)


def main():
    ruta = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    casos = (
        json.loads(ruta.read_text("utf-8"))
        if ruta
        else {
            "d_iz14": dict(iz=14, mz=-14, mx=18, ix=-14),
            "a_iz18_ty": dict(iz=18, mz=-18, mx=18, ix=-14, ity=12, mty=-12),
        }
    )

    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 800, "height": 800})
        time.sleep(0.4)
        viewer = page.query_selector("#viewer")
        free_camera(page)

        filas = []
        for nombre, kw in casos.items():
            pose = kw if "thumb" in kw or "index" in kw else cruzar(**kw)
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
            time.sleep(0.3)
            m = page.evaluate(MEASURE_JS)
            print(
                f"  {nombre:22s} s={puntuar(m):6.3f} cruce={m['cruce']:+5.2f} "
                f"gap={m['gap']:.3f} frente={m['frenteMed']:+5.2f}"
            )
            d = page.evaluate(DEDOS_JS)
            for vista, grados in VISTAS.items():
                cam(
                    page,
                    "%.4fm %.4fm %.4fm" % (d["x"], d["y"], d["z"]),
                    f"{grados}deg 86deg {max(0.30, d['r'] * 6.5):.3f}m",
                    "22deg",
                )
                salida = OUT / f"{nombre}_{vista}.png"
                viewer.screenshot(path=str(salida))
                filas.append((f"{nombre} {vista}", salida))

        browser.close()

    if REF.exists():
        filas.insert(0, ("REF lamina", REF))
    hoja(filas, OUT / "_zoom.png", cols=len(VISTAS) + (1 if REF.exists() else 0))


if __name__ == "__main__":
    main()
