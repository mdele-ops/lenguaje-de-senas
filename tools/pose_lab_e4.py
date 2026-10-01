"""E lab 4: compactar. La estructura ya es la de la referencia (nudillos
arriba, pulgar atravesado abajo); falta que las yemas se apoyen ENCIMA del
pulgar y que los cuatro dedos se lean como un bloque, tambien a la distancia
de la camara de produccion.
"""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from pose_lab_e import HAND_POS_JS, MEASURE_JS, free_camera
from pose_lab_e3 import pose_e

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_e4"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=e4"

CASES = {
    # mas nudillo = dedos mas escorzados (barras cortas) y yemas mas abajo
    "00_m60_p96_c10": pose_e(mcp=60, pip=96, conv=10),
    "01_m70_p90_c10": pose_e(mcp=70, pip=90, conv=10),
    "02_m80_p84_c10": pose_e(mcp=80, pip=84, conv=10),
    "03_m90_p78_c10": pose_e(mcp=90, pip=78, conv=10),
    "04_m80_p95_c10": pose_e(mcp=80, pip=95, conv=10),
    "05_m90_p90_c10": pose_e(mcp=90, pip=90, conv=10),
    # dedos mas juntos
    "06_m80_p84_c14": pose_e(mcp=80, pip=84, conv=14),
    "07_m80_p84_c18": pose_e(mcp=80, pip=84, conv=18),
    # pulgar: subirlo hacia las yemas y tumbarlo mas
    "08_t_z25": pose_e(mcp=80, pip=84, conv=14, t1=(-60, 25)),
    "09_t_z-15": pose_e(mcp=80, pip=84, conv=14, t1=(-60, -15)),
    "10_t_y70": pose_e(mcp=80, pip=84, conv=14, t1=(-70, 10)),
    "11_t_curl85": pose_e(mcp=80, pip=84, conv=14, tcurl=0.85, t1=(-60, 10)),
    "12_t_curl65": pose_e(mcp=80, pip=84, conv=14, tcurl=0.65, t1=(-60, 10)),
    # yema plana sobre el pulgar
    "13_dip20": pose_e(mcp=80, pip=84, dip=20, conv=14),
    "14_dip-15": pose_e(mcp=80, pip=84, dip=-15, conv=14),
}

VIEWS = {
    "frente": ("0deg 82deg 0.62m", "26deg"),
    "diag": ("-40deg 78deg 0.62m", "26deg"),
}


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="chrome",
            args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"],
        )
        page = browser.new_page(viewport={"width": 900, "height": 1200})
        page.goto(URL, wait_until="networkidle", timeout=60000)
        page.wait_for_selector("#anim-info", timeout=20000, state="attached")
        for _ in range(120):
            try:
                if page.evaluate(
                    "() => !!(window.__LSM_CONTROLLER__ && window.__LSM_CONTROLLER__.isModelReady())"
                ):
                    break
            except Exception:
                pass
            time.sleep(0.4)
        time.sleep(1.0)
        free_camera(page)

        viewer = page.query_selector("#viewer")
        for name, pose in CASES.items():
            page.evaluate(
                "(pose) => window.__LSM_CONTROLLER__.applyTestPose(pose)", pose
            )
            time.sleep(0.25)
            m = page.evaluate(MEASURE_JS)
            print(
                f"{name:16s} d={m['dI']:.3f}/{m['dM']:.3f}/{m['dR']:.3f}/{m['dP']:.3f} "
                f"over={m['overI']:+.2f}/{m['overM']:+.2f}/{m['overP']:+.2f} "
                f"gaps={m['gIM']:.2f}/{m['gMR']:.2f}/{m['gRP']:.2f}"
            )
            hand = page.evaluate(HAND_POS_JS)
            target = "%.3fm %.3fm %.3fm" % (hand["x"], hand["y"], hand["z"])
            for view, (orbit, fov) in VIEWS.items():
                page.evaluate(
                    """(a) => {
                        const mv = document.getElementById('handViewer');
                        mv.cameraTarget = a.t;
                        mv.cameraOrbit = a.orbit;
                        mv.fieldOfView = a.fov;
                        mv.jumpCameraToGoal();
                    }""",
                    {"t": target, "orbit": orbit, "fov": fov},
                )
                time.sleep(0.12)
                viewer.screenshot(path=str(OUT_DIR / f"{name}_{view}.png"))

        browser.close()


if __name__ == "__main__":
    main()
