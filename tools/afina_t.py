"""T: afinar la mejor de la rejilla, un mando cada vez.

La rejilla de `search_t.py` va a saltos gruesos y su mejor resultado se queda
pegado al borde en dos mandos (t1x en -50 y t1z en 56), que es justo el fallo
que ya costo caro en la O: con pasos gruesos el optimo esta fuera de la caja y
la busqueda no se entera.

Aqui se recorre cada mando ENTERO, de uno en uno, dejando los demas quietos, y
se repite hasta que ninguno mejora (descenso por coordenadas). Es barato
—unas 120 medidas por vuelta— y no se queda en los bordes.
"""
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from pose_lab_e import free_camera
from pose_lab_t import MEASURE_JS
from search_t import construye, linea, puntua
from ver_s import CAM_FOV, CAM_ORBIT, CAM_TARGET
import search_e9 as se9
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "afina_t"
OUT.mkdir(parents=True, exist_ok=True)

se9.URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=t8"

# La mejor de la rejilla 3, ya con la primera pasada de afinado encima.
PARTIDA = {
    "tcurl": 0.35, "t1x": -50, "t1z": 56, "t1y": 30,
    "t2x": 0, "t3x": -5, "sep": 12,
}

# Recorrido completo de cada mando, con paso fino.
RANGOS = {
    "tcurl": [round(0.05 * i, 2) for i in range(0, 13)],        # 0.00 .. 0.60
    "t1x": list(range(-85, 21, 5)),
    "t1z": list(range(15, 91, 5)),
    "t1y": list(range(-40, 61, 5)),
    "t2x": list(range(-45, 46, 5)),
    "t3x": list(range(-50, 46, 5)),
    "sep": list(range(0, 25, 2)),
}
VUELTAS = 5


def cam(page):
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
    time.sleep(0.25)


def mide(page, receta):
    page.evaluate(
        "(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", construye(receta)
    )
    time.sleep(0.05)
    return page.evaluate(MEASURE_JS)


def main():
    receta = dict(PARTIDA)
    historia = []

    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 900, "height": 900})
        time.sleep(0.4)
        free_camera(page)
        cam(page)

        m = mide(page, receta)
        mejor, _ = puntua(m)
        print(" ", linea("partida", m, mejor))

        for vuelta in range(VUELTAS):
            movio = False
            for mando, valores in RANGOS.items():
                base = receta[mando]
                mejor_val, mejor_m = base, None
                for v in valores:
                    if v == base:
                        continue
                    receta[mando] = v
                    m = mide(page, receta)
                    if m.get("error"):
                        continue
                    pts, _ = puntua(m)
                    if pts < mejor - 1e-9:
                        mejor, mejor_val, mejor_m = pts, v, m
                receta[mando] = mejor_val
                if mejor_val != base:
                    movio = True
                    print(f"  v{vuelta+1} {mando:6s} {base} -> {mejor_val}",
                          f" p={mejor:.3f}")
                    historia.append({"vuelta": vuelta + 1, "mando": mando,
                                     "valor": mejor_val, "puntos": mejor})
            if not movio:
                print(f"  vuelta {vuelta+1}: nada que mejorar, se para")
                break

        m = mide(page, receta)
        pts, detalle = puntua(m)
        print("\n ", linea("afinada", m, pts))
        print("  receta:", receta)
        print("  castigos:", {k: round(v, 3) for k, v in detalle.items() if v > 1e-6})

        browser.close()

    (OUT / "_afinada.json").write_text(
        json.dumps({"receta": receta, "puntos": pts, "medidas": m,
                    "detalle": detalle, "historia": historia}, indent=2),
        "utf-8",
    )
    print("\nDatos en", OUT)


if __name__ == "__main__":
    main()
