"""E lab 7: comprobar que el doblez es real. Compara la E actual (puño) con las
candidatas midiendo si la yema queda por debajo del nudillo (fold) y mirando la
mano de perfil, donde el doblez no se puede confundir con el escorzo.
"""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from candidates_e import pose_e
from pose_lab_e import HAND_POS_JS, MEASURE_JS, free_camera

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_e7"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=e7"

CASES = {
    "0_puno_actual": {
        "thumb": {"curl": 0.6},
        "index": {"curl": 0.9},
        "middle": {"curl": 0.9},
        "ring": {"curl": 0.9},
        "pinky": {"curl": 0.9},
    },
    "1_solo_extra": pose_e(mcp=70, pip=92, conv=0, t2x=0, tcurl=0.0, taside=0.0),
    "2_extra_pulgar": pose_e(mcp=70, pip=92, conv=0),
    "3_curl_puro": {
        "thumb": {"curl": 0.6},
        "index": {"curl": 0.55},
        "middle": {"curl": 0.55},
        "ring": {"curl": 0.55},
        "pinky": {"curl": 0.55},
    },
    "4_curl_mas_extra": {
        "thumb": {"curl": 0.6},
        "index": {"curl": 0.35},
        "middle": {"curl": 0.35},
        "ring": {"curl": 0.35},
        "pinky": {"curl": 0.35},
        "extra": pose_e(mcp=40, pip=70, conv=0)["extra"],
    },
}

VIEWS = {
    "frente": ("0deg 84deg 0.80m", "26deg"),
    "perfil": ("-80deg 84deg 0.80m", "26deg"),
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
            time.sleep(0.3)
            m = page.evaluate(MEASURE_JS)
            print(
                f"{name:16s} fold={m['foldI']:+.2f}/{m['foldM']:+.2f}/{m['foldR']:+.2f}/{m['foldP']:+.2f} "
                f"d={m['dI']:.2f}/{m['dM']:.2f} over={m['overM']:+.2f}"
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
                time.sleep(0.15)
                viewer.screenshot(path=str(OUT_DIR / f"{name}_{view}.png"))

        browser.close()


if __name__ == "__main__":
    main()
