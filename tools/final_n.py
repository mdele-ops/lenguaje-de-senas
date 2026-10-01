"""Cataloga la N (y la Ñ) como la M de dos dedos.

La N del catalogo era un puno generico (curl 0.85 en los cinco dedos), igual
que la A o la S. En la lamina la N se hace como la M pero colgando solo
indice y medio: misma caida de muneca (~150 deg en X) y anular y menique
recogidos con el pulgar encima. La Ñ hereda la forma y solo agrega el giro
de muneca que ya tenia (la tilde).
"""
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from afina_n import CASES
from final_e15 import limpiar
from pose_lab_m5 import hoja
from pose_lab_n3 import MEASURE_JS
from search_e9 import abrir
from ver_n3 import CENTRO_JS
from pose_lab_e import free_camera

ROOT = Path(__file__).resolve().parents[1]
CATALOGO = ROOT / "data" / "catalogo-lsm.json"
OUT = ROOT / "tools" / "screenshots" / "final_n"
OUT.mkdir(parents=True, exist_ok=True)
REF = ROOT / "tools" / "screenshots" / "referencia" / "N_usuario.png"

import search_e9 as se9

se9.URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=finaln"

DESC_N = (
    "Índice y medio cuelgan hacia abajo, juntos y apuntando al piso (la M "
    "con dos dedos); la muñeca se inclina para que caigan, y anular y "
    "meñique quedan cerrados con el pulgar encima."
)
DESC_ENE = (
    "Como la N —índice y medio colgando y el resto cerrado—, con un leve "
    "giro de muñeca que hace la tilde."
)

VISTAS = {"dorso": (0, 82, 1.85), "media": (-30, 82, 1.85), "lado": (-70, 82, 2.0)}


def entero(muneca):
    return {k: int(v) if float(v) == int(v) else v for k, v in muneca.items()}


def main():
    cat = json.loads(CATALOGO.read_text("utf-8"))
    n = next(x for x in cat["senas"] if x["letra"] == "N")
    ene = next(x for x in cat["senas"] if x["letra"] == "Ñ")
    antes_n = json.loads(json.dumps(n["pose"]))
    antes_ene = json.loads(json.dumps(ene["pose"]))

    nueva_n = limpiar(CASES["P4_convergen"])
    if "muneca" in nueva_n:
        nueva_n["muneca"] = entero(nueva_n["muneca"])
    nueva_ene = json.loads(json.dumps(nueva_n))
    # la tilde: mismo gesto girando la muneca, como ya estaba planteada la Ñ
    nueva_ene["muneca"] = dict(nueva_ene.get("muneca", {}), y=12)

    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 760, "height": 760})
        time.sleep(0.3)
        viewer = page.query_selector("#viewer")
        free_camera(page)

        hojas = {k: [("REF foto", REF)] for k in VISTAS}
        casos = (
            ("1_N_ANTES", antes_n),
            ("2_N_DESPUES", nueva_n),
            ("3_ENE_DESPUES", nueva_ene),
        )
        for nombre, pz in casos:
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pz)
            time.sleep(0.35)
            m = page.evaluate(MEASURE_JS)
            c = page.evaluate(CENTRO_JS)
            print(
                f"{nombre:14s} down={m['idxDown']:+.2f}/{m['midDown']:+.2f} "
                f"tog={m['togIM']:.2f} ringUp={m['ringUp']:+.2f} "
                f"pinkyUp={m['pinkyUp']:+.2f}"
            )
            for vista, (theta, phi, k) in VISTAS.items():
                page.evaluate(
                    """(a) => {
                        const mv = document.getElementById('handViewer');
                        mv.cameraTarget = a.t;
                        mv.cameraOrbit = a.orbit;
                        mv.fieldOfView = '26deg';
                        mv.jumpCameraToGoal();
                    }""",
                    {
                        "t": "%.3fm %.3fm %.3fm" % (c["x"], c["y"], c["z"]),
                        "orbit": f"{theta}deg {phi}deg {max(0.3, c['size'] * k):.3f}m",
                    },
                )
                time.sleep(0.15)
                ruta = OUT / f"{nombre}_{vista}.png"
                viewer.screenshot(path=str(ruta))
                hojas[vista].append((nombre, ruta))
        browser.close()

    for vista, items in hojas.items():
        hoja(items, OUT / f"_{vista}.png", cols=4, cell=330)

    n["pose"] = nueva_n
    n["descripcion"] = DESC_N
    ene["pose"] = nueva_ene
    ene["descripcion"] = DESC_ENE
    partes = cat["version"].split(".")
    partes[-1] = str(int(partes[-1]) + 1)
    cat["version"] = ".".join(partes)
    CATALOGO.write_text(
        json.dumps(cat, ensure_ascii=False, indent=2) + "\n", "utf-8"
    )
    print("catalogo version", cat["version"])
    (OUT / "_pose.json").write_text(
        json.dumps(
            {
                "antes_N": antes_n,
                "despues_N": nueva_n,
                "antes_Ñ": antes_ene,
                "despues_Ñ": nueva_ene,
            },
            ensure_ascii=False,
            indent=2,
        ),
        "utf-8",
    )


if __name__ == "__main__":
    main()
