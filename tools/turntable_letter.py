"""Gira la camara alrededor de una letra para ver como queda orientada la mano.

    py tools/turntable_letter.py A
"""
import json
import sys
import time

from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright

from render_letters import (
    CHROME_ARGS,
    FOV,
    HAND_CENTER_JS,
    OUT_DIR,
    crop_center_square,
    load_senas,
    open_ready_page,
    safe_name,
)

ANGLES = [0, 45, 90, 135, 180, 225, 270, 315]


def main():
    letra = (sys.argv[1] if len(sys.argv) > 1 else "A").upper()
    senas = [s for s in load_senas() if s["letra"].upper() == letra]
    if not senas:
        print("Letra no encontrada:", letra)
        return
    pose = senas[0].get("pose")

    out_dir = OUT_DIR.parent / "turntable"
    out_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(args=CHROME_ARGS)
        page = open_ready_page(browser)
        viewer = page.query_selector("#viewer")
        page.evaluate("(p) => window.__LSM_CONTROLLER__.applyTestPose(p)", pose)
        time.sleep(0.6)

        center = page.evaluate(HAND_CENTER_JS)
        target = f"{center['x']:.4f}m {center['y']:.4f}m {center['z']:.4f}m"

        shots = []
        for a in ANGLES:
            page.evaluate(
                """(o) => {
                    const mv = document.getElementById('handViewer');
                    mv.cameraTarget = o.target;
                    mv.cameraOrbit = o.orbit;
                    mv.fieldOfView = o.fov;
                    mv.jumpCameraToGoal();
                }""",
                {"target": target, "orbit": f"{a}deg 84deg 0.42m", "fov": FOV},
            )
            time.sleep(0.35)
            out = out_dir / f"{safe_name(letra)}_{a:03d}.png"
            viewer.screenshot(path=str(out))
            crop_center_square(out)
            shots.append((f"{a}deg", out))
            print("  ", letra, a)

        cell, label_h, cols = 220, 24, 4
        rows = (len(shots) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * cell, rows * (cell + label_h)), (245, 245, 247))
        draw = ImageDraw.Draw(sheet)
        for i, (label, path) in enumerate(shots):
            x, y = (i % cols) * cell, (i // cols) * (cell + label_h)
            sheet.paste(Image.open(path).convert("RGB").resize((cell, cell), Image.LANCZOS), (x, y))
            draw.rectangle([x, y + cell, x + cell, y + cell + label_h], fill=(20, 30, 50))
            draw.text((x + 8, y + cell + 7), f"{letra} {label}", fill=(255, 255, 255))
        sheet_path = out_dir / f"_turntable_{safe_name(letra)}.png"
        sheet.save(sheet_path)
        print("Turntable:", sheet_path)
        browser.close()


if __name__ == "__main__":
    main()
