"""Compara la posicion mundial de los huesos de la mano con el camera-target
que ya sabemos que encuadra bien, para saber si ambos viven en el mismo espacio."""
import time

from playwright.sync_api import sync_playwright

from render_letters import HAND_CENTER_JS, open_ready_page, CHROME_ARGS


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(args=CHROME_ARGS)
        page = open_ready_page(browser)
        print("centro mano (bones):", page.evaluate(HAND_CENTER_JS))
        print(
            "bounding box / target actual:",
            page.evaluate(
                """() => {
                    const mv = document.getElementById('handViewer');
                    const t = mv.getCameraTarget();
                    const d = mv.getDimensions ? mv.getDimensions() : null;
                    return { target: { x: t.x, y: t.y, z: t.z }, dims: d };
                }"""
            ),
        )
        time.sleep(0.2)
        browser.close()


if __name__ == "__main__":
    main()
