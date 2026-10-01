"""Lista los huesos de la mano derecha tal y como vienen en el .glb cargado."""
from playwright.sync_api import sync_playwright

from lab_e2 import abrir
from pose_lab_e import _GET_SCENE

NOMBRES_JS = (
    """
() => {
  const mv = document.getElementById('handViewer');
"""
    + _GET_SCENE
    + """
  const scene = getScene(mv);
  if (!scene) return { error: 'no-scene' };
  const out = [];
  scene.traverse((o) => { if (o && o.name && /Right(Hand|Arm|ForeArm)/.test(o.name)) out.push(o.name); });
  return out;
}
"""
)


def main():
    with sync_playwright() as p:
        browser, page = abrir(p)
        for n in page.evaluate(NOMBRES_JS):
            print(n)
        browser.close()


if __name__ == "__main__":
    main()
