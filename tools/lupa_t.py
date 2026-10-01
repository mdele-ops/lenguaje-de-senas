"""T: la muesca indice-medio con la camara pegada, no con el recorte.

Todas las capturas anteriores salen borrosas por el mismo motivo: la mano ocupa
unos 300 px del visor y el recorte los estira hasta 700. Ampliar pixeles no
inventa detalle, y en la T lo que hay que decidir cabe en ese detalle: si la
yema del pulgar se lee como pulgar asomando entre dos dedos o como un quinto
dedo pegado al indice.

Aqui se mueve la CAMARA: se apunta al punto medio de los nudillos del indice y
del medio y se baja el campo de vision, asi que el mismo bulto se dibuja con
cinco veces mas pixeles y ya no hace falta estirar nada. Se saca la T y, con el
mismo encuadre, la A y la S, que son el puno con el que se puede confundir.
"""
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from PIL import Image, ImageDraw

from enfoque_r import hoja
from mira_t import CADENAS, COLORES, PUNTOS_JS, TODOS, abrir_nitido
from pose_lab_e import _GET_SCENE, free_camera
from pose_lab_t import MEASURE_JS
from search_t import construye, linea, puntua
from ver_s import CAM_FOV, CAM_ORBIT, CAM_TARGET
import search_e9 as se9

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "lupa_t"
OUT.mkdir(parents=True, exist_ok=True)
AFINADA = ROOT / "tools" / "screenshots" / "afina_t" / "_afinada.json"

se9.URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=t10"

# Centro del encuadre: la muesca entre indice y medio, que es donde pasa todo.
MUESCA_JS = (
    """
() => {
  const mv = document.getElementById('handViewer');
"""
    + _GET_SCENE
    + """
  const scene = getScene(mv);
  if (!scene) return null;
  scene.updateMatrixWorld(true);
  const B = {};
  scene.traverse((o) => { if (o && o.name) B[o.name] = o; });
  const p = (n) => {
    const e = B[n].matrixWorld.elements;
    return [e[12], e[13], e[14]];
  };
  const a = p('mixamorig1RightHandIndex2_041');
  const b = p('mixamorig1RightHandMiddle2_045');
  // `cameraTarget` va en el sistema del visor, que lleva la escena centrada:
  // sin restar ese desplazamiento la camara apunta a la bota del personaje.
  const off = (scene.target && scene.target.position) || { x: 0, y: 0, z: 0 };
  return [(a[0]+b[0])/2 - off.x, (a[1]+b[1])/2 - off.y, (a[2]+b[2])/2 - off.z];
}
"""
)

# Vistas: de frente es la que decide, las otras dos confirman que el pulgar
# esta metido y no solo tapando.
VISTAS = (("frente", "0deg 84deg 1.05m"),
          ("alto", "0deg 66deg 1.05m"),
          ("lado", "-42deg 82deg 1.05m"))
FOV = "13deg"


def cam(page, centro, orbit):
    page.evaluate(
        """(a) => {
            const mv = document.getElementById('handViewer');
            mv.cameraTarget = a.t;
            mv.cameraOrbit = a.orbit;
            mv.fieldOfView = a.fov;
            mv.jumpCameraToGoal();
        }""",
        {
            "t": "%.4fm %.4fm %.4fm" % tuple(centro),
            "orbit": orbit,
            "fov": FOV,
        },
    )
    time.sleep(0.3)


def cam_app(page):
    """La camara de la aplicacion: es con la que valen las medidas.

    Las de `VISTAS` estan pegadas a la mano, y con el campo de vision tan
    estrecho la perspectiva cambia: camDesvio y camCima medidos ahi no son los
    de la lamina. Sirven para mirar, no para puntuar.
    """
    page.evaluate(
        """(a) => {
            const mv = document.getElementById('handViewer');
            mv.cameraTarget = a.t;
            mv.cameraOrbit = a.orbit;
            mv.fieldOfView = a.fov;
            mv.jumpCameraToGoal();
        }""",
        {"t": CAM_TARGET, "orbit": CAM_ORBIT, "fov": CAM_FOV},
    )
    time.sleep(0.3)


def con_esqueleto(page, ruta):
    """Captura del visor entero con los huesos encima, sin recortar."""
    datos = page.evaluate(PUNTOS_JS, TODOS)
    page.query_selector("#handViewer").screenshot(path=str(ruta))
    if datos.get("error"):
        return
    im = Image.open(ruta).convert("RGB")
    ex, ey = im.width / datos["w"], im.height / datos["h"]
    d = ImageDraw.Draw(im)
    for dedo, cadena in CADENAS.items():
        col = COLORES[dedo]
        seq = [(datos["pts"][n][0] * ex, datos["pts"][n][1] * ey)
               for n in cadena if n in datos["pts"]]
        if len(seq) > 1:
            d.line(seq, fill=col, width=3)
        for i, pt in enumerate(seq):
            r = 9 if (dedo == "pulgar" and i == len(seq) - 1) else 5
            d.ellipse([pt[0]-r, pt[1]-r, pt[0]+r, pt[1]+r], fill=col)
    im.save(ruta)


def main():
    catalogo = json.loads((ROOT / "data" / "catalogo-lsm.json").read_text("utf-8"))
    por_letra = {s["letra"]: s for s in catalogo["senas"]}
    receta = json.loads(AFINADA.read_text("utf-8"))["receta"]

    poses = [("T", construye(receta)), ("A", por_letra["A"]["pose"]),
             ("S", por_letra["S"]["pose"])]

    with sync_playwright() as p:
        browser, page = abrir_nitido(p, lado=700, escala=2)
        free_camera(page)

        items = []
        for etiqueta, pose in poses:
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
            time.sleep(0.4)
            centro = page.evaluate(MUESCA_JS)
            if centro is None:
                print("  no se pudo localizar la muesca")
                break
            if etiqueta == "T":
                cam_app(page)
                m = page.evaluate(MEASURE_JS)
                print(" ", linea("T afinada", m, puntua(m)[0]))
            for vista, orbit in VISTAS:
                cam(page, centro, orbit)
                ruta = OUT / f"{etiqueta}_{vista}.png"
                page.query_selector("#handViewer").screenshot(path=str(ruta))
                items.append((f"{etiqueta} {vista}", ruta))
            if etiqueta == "T":
                cam(page, centro, VISTAS[0][1])
                ruta = OUT / "T_frente_esq.png"
                con_esqueleto(page, ruta)
                items.append(("T frente esq", ruta))

        browser.close()

    hoja(items, OUT / "_hoja.png", cols=4, cell=430,
         titulo="T de cerca (camara pegada a la muesca) contra A y S")
    print("Capturas en", OUT)


if __name__ == "__main__":
    main()
