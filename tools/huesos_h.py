"""Lista los nodos de la mano derecha de model2.glb tal como los ve el visor."""
import json

from playwright.sync_api import sync_playwright

import lab

DUMP_JS = """
() => {
  const mv = document.getElementById('handViewer');
  function getScene(m) {
    if (m.model && typeof m.model.traverse === 'function') return m.model;
    if (m.model && m.model.scene && typeof m.model.scene.traverse === 'function') return m.model.scene;
    for (const s of Object.getOwnPropertySymbols(m)) {
      const v = m[s];
      if (v && typeof v.traverse === 'function') return v;
      if (v && v.model && typeof v.model.traverse === 'function') return v.model;
      if (v && v.target && typeof v.target.traverse === 'function') return v.target;
    }
    return null;
  }
  const scene = getScene(mv);
  const out = [];
  scene.traverse((o) => { if (o && o.name && /Hand|Arm|Shoulder/i.test(o.name)) out.push(o.name); });
  return out;
}
"""


def main():
    catalog = lab.load_catalog()
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", args=lab.CHROME_ARGS)
        page = lab.open_lab(browser, catalog)
        print(json.dumps(page.evaluate(DUMP_JS), indent=1, ensure_ascii=False))
        browser.close()


if __name__ == "__main__":
    main()
