"""E lab 3: partiendo del reparto que ya dobla bien (MCP ~60, PIP ~90), busca
cuanto hay que cerrar para que las yemas se apoyen en el pulgar y cuanto
spread hace falta para que los cuatro dedos se lean como un bloque.
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
    T2,
    T3,
    free_camera,
)

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "screenshots" / "lab_e3"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8123/practica.html?letra=%E2%97%8B&v=e3"

FAN = (-1.5, -0.5, 0.5, 1.5)


def pose_e(
    mcp=60,
    pip=90,
    dip=0,
    conv=0,
    tcurl=0.74,
    taside=-0.5,
    t1=(-60, 0),
    t2x=0,
    t3x=0,
    arm_z=-18,
    wrist=None,
):
    """conv junta las yemas (grados de spread repartidos en abanico)."""
    extra = {ARM: {"z": arm_z}, T1: {"y": t1[0], "z": t1[1]}}
    for f in FINGERS:
        b = BONES[f]
        extra[b[0]] = {"x": mcp}
        extra[b[1]] = {"x": pip}
        if dip:
            extra[b[2]] = {"x": dip}
    if t2x:
        extra[T2] = {"x": t2x}
    if t3x:
        extra[T3] = {"x": t3x}

    pose = {"thumb": {"curl": tcurl, "aside": taside}, "extra": extra}
    for i, f in enumerate(FINGERS):
        pose[f] = {"curl": 0.0, "spread": FAN[i] * conv}
    if wrist:
        pose["muneca"] = dict(wrist)
    return pose


CASES = {
    "00_base": pose_e(),
    # cerrar mas la mano: reparto MCP/PIP
    "01_m66_p96": pose_e(mcp=66, pip=96),
    "02_m72_p100": pose_e(mcp=72, pip=100),
    "03_m60_p105": pose_e(mcp=60, pip=105),
    "04_m70_p90_d20": pose_e(mcp=70, pip=90, dip=20),
    "05_m66_p96_d15": pose_e(mcp=66, pip=96, dip=15),
    # juntar los dedos
    "06_conv6": pose_e(mcp=66, pip=96, conv=6),
    "07_conv10": pose_e(mcp=66, pip=96, conv=10),
    "08_conv_neg6": pose_e(mcp=66, pip=96, conv=-6),
    # subir/tumbar el pulgar para que reciba las yemas
    "09_t_z20": pose_e(mcp=66, pip=96, t1=(-60, 20)),
    "10_t_z40": pose_e(mcp=66, pip=96, t1=(-60, 40)),
    "11_t_y45": pose_e(mcp=66, pip=96, t1=(-45, 20)),
    "12_t_curl85": pose_e(mcp=66, pip=96, tcurl=0.85, t1=(-60, 20)),
    "13_t_curl60_t2": pose_e(mcp=66, pip=96, tcurl=0.6, t1=(-60, 20), t2x=-20),
}

VIEWS = {
    "frente": ("0deg 82deg 0.62m", "26deg"),
    "perfil": ("-80deg 82deg 0.62m", "26deg"),
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
                f"gaps={m['gIM']:.2f}/{m['gMR']:.2f}/{m['gRP']:.2f} "
                f"tHoriz={m['tHoriz']:.2f}"
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
