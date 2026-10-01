"""Estado actual de la C: fotos desde varias orbitas y medidas del pulgar."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from playwright.sync_api import sync_playwright

import c_lab
import lab

lab.URL = lab.URL.replace(":8123", ":8006")

# El modelo actual ya no trae los sufijos "mixamorig1..._0NN" que mapea lab.py.
lab.BONES = {
    lado: {
        "arm": f"{L}Arm",
        "fore": f"{L}ForeArm",
        "wrist": f"{L}Hand",
        "thumb": [f"{L}HandThumb{i}" for i in range(1, 5)],
        "index": [f"{L}HandIndex{i}" for i in range(1, 5)],
        "middle": [f"{L}HandMiddle{i}" for i in range(1, 5)],
        "ring": [f"{L}HandRing{i}" for i in range(1, 5)],
        "pinky": [f"{L}HandPinky{i}" for i in range(1, 5)],
    }
    for lado, L in (("right", "Right"), ("left", "Left"))
}

OUT = Path(__file__).resolve().parent / "screenshots" / "pulgar_c"

ORBITS = [-30, 0, 30, 60, 90]


def main():
    catalog = lab.load_catalog()
    sena = next(s for s in catalog["senas"] if s["letra"] == "C")
    pose = sena["pose"]
    print("pose C en disco:")
    print("  thumb:", pose["thumb"])
    print("  extra pulgar:", {k: v for k, v in pose["extra"].items() if "Thumb" in k})

    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = c_lab.launch(p)
        # A veces el modelo queda listo antes de que se apliquen las
        # correcciones de reposo del brazo (rig.restCorrections, que solo
        # corren una vez): el brazo se queda en T-pose y la foto no sirve.
        # Con la postura buena la normal de la palma queda horizontal.
        for intento in range(1, 6):
            page = lab.open_lab(browser, catalog)
            unit = c_lab.scales(page)
            lab.apply_pose(page, pose)
            m = c_lab.metrics(page, unit)
            if abs(m["palma_x"]) > 0.9:
                break
            print(f"  intento {intento}: brazo sin corregir (palma_x={m['palma_x']}), recargando")
            page.close()
        else:
            raise RuntimeError("El brazo nunca cargo en la postura corregida")
        print("metricas:", m)

        shots = []
        for deg in ORBITS:
            out = OUT / f"orbit_{deg:+04d}.png"
            lab.shot(page, out, orbit=f"{deg}deg 84deg {lab.RADIUS}", side="right")
            shots.append((f"{deg}deg", out))
            print("  foto", deg, flush=True)

        lab.sheet(shots, OUT / "_hoja.png", cols=5, cell=300)
        browser.close()


if __name__ == "__main__":
    main()
