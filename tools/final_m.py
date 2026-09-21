"""Escribe en el catalogo la M de la foto: tres lomos sobre el pulgar.

La M del catalogo era un puno generico (curl 0.85 en los cinco dedos). En la
lamina el pulgar cruza la palma y se mete BAJO indice, medio y anular; la yema
asoma entre anular y menique; el menique va mas cerrado, a un lado.

El pulgar no se consigue con twist: hace falta orientar Thumb1 y alargarlo
hasta across ~0.78. Los tres lomos se igualan con extra por falange porque el
curl solo deja el anular mas abierto que el indice (MCP 63 vs 75, DIP 67 vs 40).
"""
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from final_e15 import limpiar
import hoja_e
from hoja_e import preparar, publicar, retratar
from pose_lab_m5 import MEASURE_JS
from pose_lab_m7 import CASES
from pulgar_e import PULGAR_JS
from pulgar_e import linea as linea_pulgar
from search_e9 import abrir
from simetria_e import SIMETRIA_JS, detalle, informe

ROOT = Path(__file__).resolve().parents[1]
CATALOGO = ROOT / "data" / "catalogo-lsm.json"
OUT = ROOT / "tools" / "screenshots" / "final_m"
hoja_e.REFERENCIAS = [
    ("REF foto", ROOT / "tools" / "screenshots" / "referencia" / "M_usuario.png")
]

DESCRIPCION = (
    "Palma al frente: indice, medio y anular se doblan juntos sobre el pulgar "
    "y forman tres lomos; el pulgar queda debajo y su yema asoma entre el "
    "anular y el menique; el menique va cerrado a un lado."
)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cat = json.loads(CATALOGO.read_text("utf-8"))
    sena = next(x for x in cat["senas"] if x["letra"] == "M")
    anterior = json.loads(json.dumps(sena["pose"]))
    nueva = limpiar(CASES["B_eq72"])

    with sync_playwright() as p:
        browser, page = abrir(p)
        viewer = preparar(page)

        def aplicar(pz):
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pz)
            time.sleep(0.35)

        salida = {}
        aplicar(anterior)
        s = page.evaluate(SIMETRIA_JS)
        m = page.evaluate(PULGAR_JS)
        g = page.evaluate(MEASURE_JS)
        print("ANTES ", informe("M", s))
        print(detalle(s))
        print(
            f"      across={m['across4']:+.2f} frente={m['frente4']:+.2f} "
            f"dI={g['dI']:.2f} dM={g['dM']:.2f} dR={g['dR']:.2f}"
        )
        retratar(page, viewer, "1_ANTES", OUT, salida)

        aplicar(nueva)
        s = page.evaluate(SIMETRIA_JS)
        m = page.evaluate(PULGAR_JS)
        g = page.evaluate(MEASURE_JS)
        print("DESPUES", informe("M", s))
        print(detalle(s))
        print(
            f"      across={m['across4']:+.2f} frente={m['frente4']:+.2f} "
            f"dI={g['dI']:.2f} dM={g['dM']:.2f} dR={g['dR']:.2f}"
        )
        print("      ", linea_pulgar("pulgar", m, 0))
        retratar(page, viewer, "2_DESPUES", OUT, salida)
        browser.close()

    sena["pose"] = nueva
    sena["descripcion"] = DESCRIPCION
    partes = cat["version"].split(".")
    partes[-1] = str(int(partes[-1]) + 1)
    cat["version"] = ".".join(partes)
    CATALOGO.write_text(
        json.dumps(cat, ensure_ascii=False, indent=2) + "\n", "utf-8"
    )
    print("\ncatalogo ->", CATALOGO, "version", cat["version"])

    publicar(salida, OUT, cols=3, cell=320)
    (OUT / "_pose.json").write_text(
        json.dumps({"antes": anterior, "despues": nueva}, indent=2), "utf-8"
    )


if __name__ == "__main__":
    main()
