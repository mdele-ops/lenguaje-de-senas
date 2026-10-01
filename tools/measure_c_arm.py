"""Mide mundo: que eje saca la mano del torso."""
import time

from playwright.sync_api import sync_playwright

URL = "http://localhost:8123/practica.html?letra=C&v=cmeas"

ARM = "mixamorig1RightArm_033"
FORE = "mixamorig1RightForeArm_034"
HAND = "mixamorig1RightHand_035"
SPINE = "mixamorig1Spine2_03"
I1 = "mixamorig1RightHandIndex1_040"
M1 = "mixamorig1RightHandMiddle1_044"
R1 = "mixamorig1RightHandRing1_048"
P1 = "mixamorig1RightHandPinky1_052"
T1 = "mixamorig1RightHandThumb1_036"

BASE = {
    "thumb": {"curl": 0.32, "aside": 0.74},
    "index": {"curl": 0.4, "spread": -4},
    "middle": {"curl": 0.4, "spread": 3},
    "ring": {"curl": 0.4, "spread": 4},
    "pinky": {"curl": 0.4, "spread": 6},
    "extra": {
        I1: {"x": 12},
        M1: {"x": 12},
        R1: {"x": 12},
        P1: {"x": 12},
        T1: {"y": 20},
    },
}


def with_extra(**bones):
    pose = {
        "thumb": dict(BASE["thumb"]),
        "index": dict(BASE["index"]),
        "middle": dict(BASE["middle"]),
        "ring": dict(BASE["ring"]),
        "pinky": dict(BASE["pinky"]),
        "extra": dict(BASE["extra"]),
    }
    pose["extra"].update(bones)
    return pose


CASES = {
    "reposo": BASE,
    "clip_old": with_extra(**{ARM: {"z": -22, "y": -38}, FORE: {"x": 26, "y": -18}}),
    "arm_y+20": with_extra(**{ARM: {"y": 20}}),
    "arm_y+35": with_extra(**{ARM: {"y": 35}}),
    "arm_y-20": with_extra(**{ARM: {"y": -20}}),
    "arm_z+20": with_extra(**{ARM: {"z": 20}}),
    "arm_z-20": with_extra(**{ARM: {"z": -20}}),
    "arm_x+20": with_extra(**{ARM: {"x": 20}}),
    "arm_x-20": with_extra(**{ARM: {"x": -20}}),
    "fore_y+25": with_extra(**{FORE: {"y": 25}}),
    "fore_y-25": with_extra(**{FORE: {"y": -25}}),
    "fore_z+25": with_extra(**{FORE: {"z": 25}}),
    "fore_z-25": with_extra(**{FORE: {"z": -25}}),
    "fore_x+20": with_extra(**{FORE: {"x": 20}}),
    "y35_z12": with_extra(**{ARM: {"y": 35, "z": 12}}),
    "y30_x-15": with_extra(**{ARM: {"y": 30, "x": -15}}),
}


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="chrome",
            args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"],
        )
        page = browser.new_page(viewport={"width": 900, "height": 700})
        page.goto(URL, wait_until="networkidle")
        page.wait_for_selector("#anim-info", timeout=20000, state="attached")
        time.sleep(7)
        for _ in range(50):
            if page.evaluate(
                "() => window.__LSM_CONTROLLER__ && window.__LSM_CONTROLLER__.isModelReady()"
            ):
                break
            time.sleep(0.3)
        time.sleep(2.3)

        def world(name):
            return page.evaluate(
                "(n) => window.__LSM_CONTROLLER__.getBoneWorld(n)", name
            )

        print("bone names sample", page.evaluate(
            """() => {
                const c = window.__LSM_CONTROLLER__;
                return c.getBoneWorld('mixamorig1RightHand_035');
            }"""
        ))

        for name, pose in CASES.items():
            page.evaluate(
                "(pose) => window.__LSM_CONTROLLER__.applyTestPose(pose)", pose
            )
            time.sleep(0.15)
            spine = world(SPINE)
            hand = world(HAND)
            arm = world(ARM)
            print(
                f"{name:12} spine={spine} arm={arm} hand={hand}"
            )

        browser.close()


if __name__ == "__main__":
    main()
