"""E lab 6: el pulgar. Con los dedos fijos en un doblez de E, busca la
rotacion que deja el pulgar TUMBADO y atravesado sobre la palma (como en la
referencia), no levantado hacia arriba como en la B.
"""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from pose_lab_e import ARM, BONES, FINGERS, HAND_POS_JS, MEASURE_JS, T1, T2, T3, free_camera

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_e6"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=e6"

FAN = (-1.5, -0.5, 0.5, 1.5)
MCP, PIP, DIP, CONV = 70, 92, 0, 12


def pose_t(tcurl=0.6, taside=-0.5, t1=(-60, 0), t2x=0, t3x=0, arm_z=-18):
    extra = {ARM: {"z": arm_z}, T1: {"y": t1[0], "z": t1[1]}}
    for f in FINGERS:
        b = BONES[f]
        extra[b[0]] = {"x": MCP}
        extra[b[1]] = {"x": PIP}
        if DIP:
            extra[b[2]] = {"x": DIP}
    if t2x:
        extra[T2] = {"x": t2x}
    if t3x:
        extra[T3] = {"x": t3x}
    pose = {"thumb": {"curl": tcurl, "aside": taside}, "extra": extra}
    for i, f in enumerate(FINGERS):
        pose[f] = {"curl": 0.0, "spread": FAN[i] * CONV}
    return pose


CASES = {
    "00_b_like": pose_t(),
    "01_curl30": pose_t(tcurl=0.3),
    "02_curl80": pose_t(tcurl=0.8),
    "03_curl100": pose_t(tcurl=1.0),
    "04_y20": pose_t(t1=(-20, 0)),
    "05_y40": pose_t(t1=(-40, 0)),
    "06_y80": pose_t(t1=(-80, 0)),
    "07_aside0": pose_t(taside=0.0),
    "08_aside40": pose_t(taside=0.4),
    "09_t2x30": pose_t(t2x=30),
    "10_t2x60": pose_t(t2x=60),
    "11_t2x_-30": pose_t(t2x=-30),
    "12_z25": pose_t(t1=(-60, 25)),
    "13_z-25": pose_t(t1=(-60, -25)),
    "14_mix": pose_t(tcurl=0.35, taside=0.0, t1=(-70, 0), t2x=45),
    "15_mix2": pose_t(tcurl=0.5, taside=-0.2, t1=(-80, -15), t2x=30),
}

VIEWS = {
    "frente": ("0deg 82deg 0.62m", "26deg"),
    "diag": ("35deg 78deg 0.62m", "26deg"),
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
                f"{name:12s} d={m['dI']:.3f}/{m['dM']:.3f}/{m['dR']:.3f}/{m['dP']:.3f} "
                f"over={m['overI']:+.2f}/{m['overM']:+.2f} tHoriz={m['tHoriz']:.2f}"
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
