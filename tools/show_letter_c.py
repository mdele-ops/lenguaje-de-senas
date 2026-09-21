"""Abre Chrome visible, espera el modelo y pulsa la letra C."""
import time

from playwright.sync_api import sync_playwright

URL = "http://localhost:8123/practica.html?letra=C&v=showc9"


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="chrome",
            headless=False,
            args=["--start-maximized"],
        )
        context = browser.new_context(no_viewport=True)
        page = context.new_page()
        page.goto(URL, wait_until="networkidle")
        page.wait_for_selector("#anim-info", timeout=20000, state="attached")

        for _ in range(60):
            if page.evaluate(
                "() => window.__LSM_CONTROLLER__ && window.__LSM_CONTROLLER__.isModelReady()"
            ):
                break
            time.sleep(0.3)

        page.wait_for_selector(".letter-pill", timeout=15000)
        page.locator("button.letter-pill", has_text="C").first.click()
        print("Letra C seleccionada. Deja esta ventana abierta para verla.")
        page.wait_for_timeout(30 * 60 * 1000)


if __name__ == "__main__":
    main()
