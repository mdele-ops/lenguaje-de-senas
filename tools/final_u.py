"""U final: tres candidatas con brazo en reposo (dedos hacia arriba).

arm_z=-18 tuerce la mano y los dedos dejan de apuntar arriba, que es lo que
pide la foto. Aqui se comparan juntas vs catalogo, esperando a que acabe la
transicion de carga, en la camara de produccion.
"""
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from eje_r import CAM_FOV, CAM_ORBIT, CAM_TARGET, cam, encuadrar
from enfoque_r import MANO, captura, hoja
from pose_lab_e import free_camera
from pose_lab_r import MEASURE_JS
from pose_lab_u import linea, pose_u
from search_e9 import abrir
import search_e9 as se9

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "final_u"
OUT.mkdir(parents=True, exist_ok=True)
REF = ROOT / "tools" / "screenshots" / "lab_u2" / "_ref.png"
CATALOGO = ROOT / "data" / "catalogo-lsm.json"

se9.URL = "http://127.0.0.1:8006/practica.html?letra=%E2%97%8B&v=ufin"

FINALISTAS = {
    "A_z6": pose_u(iz=6, mz=-6, arm_z=0),
    "B_z8": pose_u(iz=8, mz=-8, arm_z=0),
    "C_par8_9": pose_u(iz=8, mz=-9, iz2=-5, mz2=5, arm_z=0),
}

DESCRIPCION = (
    "Índice y medio estirados hacia arriba y pegados en toda su longitud, "
    "sin cruzarse: es lo que la distingue de la V, donde esos dos dedos se "
    "abren, y de la R, donde se cruzan. Anular y meñique se recogen en el "
    "puño con el pulgar tumbado encima, apoyado sobre las falanges de esos dos."
)


def guardar(pose):
    datos = json.loads(CATALOGO.read_text(encoding="utf-8"))
    sena = next(s for s in datos["senas"] if s["letra"] == "U")
    sena["pose"] = pose
    sena["descripcion"] = DESCRIPCION
    partes = datos["version"].split(".")
    partes[-1] = str(int(partes[-1]) + 1)
    datos["version"] = ".".join(partes)
    CATALOGO.write_text(
        json.dumps(datos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Catalogo actualizado (version {datos['version']})")


def main():
    catalogo = json.loads(CATALOGO.read_text(encoding="utf-8"))
    vieja = next(s for s in catalogo["senas"] if s["letra"] == "U")["pose"]
    casos = {"00_catalogo": vieja, **FINALISTAS}

    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 900, "height": 900})
        time.sleep(2.2)
        free_camera(page)
        viewer = page.query_selector("#viewer")

        items = [("REF foto", REF)] if REF.exists() else []
        for nombre, pose in casos.items():
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
            time.sleep(0.45)
            m = page.evaluate(MEASURE_JS)
            print(" ", linea(nombre, m) if not m.get("error") else (nombre, m))
            cam(page, CAM_TARGET, CAM_ORBIT, CAM_FOV)
            visor = OUT / f"{nombre}_prod.png"
            viewer.screenshot(path=str(visor))
            items.append((nombre, visor))
            encuadrar(page, 0)
            mano = OUT / f"{nombre}_mano.png"
            captura(page, mano, MANO, margen=0.22, lado=520)
            items.append((nombre + " mano", mano))

        browser.close()

    hoja(items, OUT / "_hoja.png", cols=3, cell=380, titulo="U · finalistas")
    (OUT / "_poses.json").write_text(
        json.dumps(FINALISTAS, indent=2), encoding="utf-8"
    )
    print("Capturas en", OUT)


if __name__ == "__main__":
    import sys

    main()
    if "--guardar" in sys.argv:
        cual = "C_par8_9"
        if len(sys.argv) > sys.argv.index("--guardar") + 1:
            cual = sys.argv[sys.argv.index("--guardar") + 1]
        guardar(FINALISTAS[cual])
