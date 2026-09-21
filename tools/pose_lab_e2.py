"""E lab 2: diagnostico. Aisla MCP, PIP y DIP para ver hacia donde dobla cada
falange en este rig antes de repartir la flexion de la E.
"""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from pose_lab_e import (
    ARM,
    BONES,
    FINGERS,
    HAND_POS_JS,
    MEASURE_JS,
    T1,
    free_camera,
)

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_e2"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=e2"


def solo(mcp=0, pip=0, dip=0, thumb=True):
    """Pose con los dedos rectos salvo la falange que se quiere observar."""
    extra = {ARM: {"z": -18}}
    for f in FINGERS:
        b = BONES[f]
        if mcp:
            extra[b[0]] = {"x": mcp}
        if pip:
            extra[b[1]] = {"x": pip}
        if dip:
            extra[b[2]] = {"x": dip}
    pose = {
        "thumb": {"curl": 0.74, "aside": -0.5} if thumb else {"curl": 0.0},
        "extra": extra,
    }
    if thumb:
        pose["extra"][T1] = {"y": -60}
    for f in FINGERS:
        pose[f] = {"curl": 0.0}
    return pose


CASES = {
    "a0_recto": solo(),
    "a1_mcp30": solo(mcp=30),
    "a2_mcp60": solo(mcp=60),
    "a3_mcp90": solo(mcp=90),
    "b1_pip45": solo(pip=45),
    "b2_pip90": solo(pip=90),
    "b3_pip120": solo(pip=120),
    "c1_dip45": solo(dip=45),
    "d1_mcp60_pip90": solo(mcp=60, pip=90),
    "d2_mcp75_pip100_dip25": solo(mcp=75, pip=100, dip=25),
    "d3_mcp90_pip95_dip20": solo(mcp=90, pip=95, dip=20),
}

VIEWS = {
    "frente": ("0deg 82deg 0.62m", "26deg"),
    "perfil": ("-80deg 82deg 0.62m", "26deg"),
    "arriba": ("0deg 40deg 0.62m", "26deg"),
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
                f"{name:20s} dM={m['dM']:.3f} overM={m['overM']:+.3f} "
                f"knuckM={m['knuckM']:+.3f}"
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
