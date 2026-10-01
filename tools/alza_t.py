"""T: cuanto pulgar se VE, medido sobre el render y no sobre los huesos.

`camCima` mide el hueso de la yema contra el hueso mas alto de los dedos, y por
eso enganaba: los huesos van por el centro de la carne. El hueso del indice
esta medio dedo por debajo de lo alto del indice, mientras que el de la yema
del pulgar esta casi en la punta. Resultado: camCima +0.116 (el pulgar asoma un
buen trozo, segun el numero) y en el render la yema queda a ras de los nudillos.

Aqui se mide lo que se ve. Se dibuja UNA vez el mismo puno con el pulgar
apartado del hueco —los dedos no cambian, solo el pulgar— y cada candidata se
resta de esa referencia: los pixeles que cambian son pulgar visible, y de ahi
salen dos numeros honestos:

  asomaPx   cuanto sube el pulgar por encima de la silueta de los dedos
  altoPx    cuanto pulgar se ve en total (en la lamina es ~0.45 de puno)

Las dos van divididas por el ancho del puno en pixeles, para poder compararlas
con la lamina.
"""
import itertools
import json
import time
from pathlib import Path

from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright

from enfoque_r import hoja
from lupa_t import FOV, MUESCA_JS, cam, cam_app
from mira_t import abrir_nitido
from pose_lab_e import free_camera
from pose_lab_t import MEASURE_JS
from search_t import construye, linea, puntua
import search_e9 as se9

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "alza_t"
OUT.mkdir(parents=True, exist_ok=True)
AFINADA = ROOT / "tools" / "screenshots" / "afina_t" / "_afinada.json"

se9.URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=t11"

ORBIT = "0deg 84deg 1.05m"

# El pulgar apartado: mismo puno, pulgar caido por fuera del indice y sin
# levantar. Sirve de fondo contra el que restar.
FUERA = {"tcurl": 0.55, "t1x": 40, "t1z": -30, "t1y": -20,
         "t2x": 20, "t3x": 20}

# Lo que se prueba: los dos mandos que suben el pulgar. tcurl bajo = pulgar
# estirado (mas largo, asoma mas); t1x negativo = mas de pie.
BARRIDO = {
    "tcurl": (0.05, 0.15, 0.25, 0.35),
    "t1x": (-70, -62, -55, -48),
}

UMBRAL = 26  # diferencia de gris a partir de la cual el pixel es pulgar


def dibuja(page, pose, centro, ruta):
    page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
    time.sleep(0.35)
    cam(page, centro, ORBIT)
    page.query_selector("#handViewer").screenshot(path=str(ruta))
    return Image.open(ruta).convert("RGB")


def mide_visible(fondo, cand):
    """Caja del pulgar visible, en pixeles de la captura."""
    dif = ImageChops.difference(fondo, cand).convert("L").point(
        lambda v: 255 if v > UMBRAL else 0
    )
    caja = dif.getbbox()
    return caja, dif


def main():
    receta = dict(json.loads(AFINADA.read_text("utf-8"))["receta"])

    with sync_playwright() as p:
        browser, page = abrir_nitido(p, lado=700, escala=2)
        free_camera(page)

        # El encuadre se fija con la pose de partida y no se vuelve a tocar:
        # si la camara se moviera entre capturas la resta no valdria nada.
        page.evaluate(
            "(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", construye(receta)
        )
        time.sleep(0.4)
        centro = page.evaluate(MUESCA_JS)

        fuera = dict(receta, **FUERA)
        fondo = dibuja(page, construye(fuera), centro, OUT / "_sin_pulgar.png")

        # Ancho del puno en pixeles de ESTA captura, para dar las medidas en
        # unidades de puno como en la lamina.
        cam(page, centro, ORBIT)
        anchoPx = page.evaluate(
            """() => {
                const mv = document.getElementById('handViewer');
                return mv.getBoundingClientRect().width;
            }"""
        )

        items = [("sin pulgar", OUT / "_sin_pulgar.png")]
        filas = []
        claves = list(BARRIDO)
        for combo in itertools.product(*(BARRIDO[k] for k in claves)):
            r = dict(receta, **dict(zip(claves, combo)))
            etiqueta = "_".join(f"{k}{r[k]}" for k in claves)
            ruta = OUT / f"{etiqueta}.png"
            im = dibuja(page, construye(r), centro, ruta)
            caja, dif = mide_visible(fondo, im)
            dif.save(OUT / f"{etiqueta}_dif.png")

            cam_app(page)
            m = page.evaluate(MEASURE_JS)
            cam(page, centro, ORBIT)

            if caja is None:
                print("  ", etiqueta, "no se ve nada de pulgar")
                continue
            alto = (caja[3] - caja[1]) / anchoPx
            filas.append({"receta": r, "caja": caja, "altoRel": alto,
                          "camCima": m["camCima"], "camDesvio": m["camDesvio"],
                          "gapIdxPunta": m["gapIdxPunta"],
                          "gapMedPunta": m["gapMedPunta"],
                          "puntos": puntua(m)[0]})
            print(f"  {etiqueta:22s} visible={alto:.3f} caja={caja} "
                  + linea("", m, puntua(m)[0]))
            items.append((f"{etiqueta} v={alto:.2f}", ruta))

        browser.close()

    hoja(items, OUT / "_hoja.png", cols=5, cell=380,
         titulo="T: cuanto pulgar se ve segun tcurl y t1x")
    (OUT / "_filas.json").write_text(json.dumps(filas, indent=2), "utf-8")
    print("Capturas en", OUT)


if __name__ == "__main__":
    main()
