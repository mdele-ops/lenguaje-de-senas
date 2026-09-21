"""Renderiza las poses candidatas de tools/candidates.json y arma una hoja.

candidates.json = { "etiqueta": { ...pose... }, ... }

Cada etiqueta puede llevar el sufijo "@orbita" para verla desde otro angulo,
p. ej. "C perfil@70deg 84deg 0.42m".
"""
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

import lab

ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = ROOT / "tools" / "candidates.json"
OUT = ROOT / "tools" / "screenshots" / "try"


def main():
    data = json.loads(CANDIDATES.read_text(encoding="utf-8"))
    catalog = lab.load_catalog()
    OUT.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(args=lab.CHROME_ARGS)
        page = lab.open_lab(browser, catalog)

        items = []
        for i, (label, pose) in enumerate(data.items()):
            name, _, orbit = label.partition("@")
            orbit = orbit or f"0deg 84deg {lab.RADIUS}"
            lab.apply_pose(page, pose)
            v = lab.vectors(page)
            o = lab.orientation(v)
            # x crece hacia la derecha del espectador; sirve para ver de que
            # lado queda cada dedo y si estan juntos o separados.
            tips = " ".join(
                f"{k[0].upper()}{v[k + 'Tip'][0]:+.3f}"
                for k in ("thumb", "index", "middle", "ring", "pinky")
            )
            pinza = lab.length(lab.sub(v["thumbTip"], v["indexTip"]))
            print(
                f"{name:28s} dedos={lab.r3(o['dedos'])} palma={lab.r3(o['palma'])} "
                f"pinza={pinza:.3f} tips[x] {tips}"
            )
            path = OUT / f"{i:02d}_{name.replace(' ', '_').replace('/', '-')}.png"
            lab.shot(page, path, orbit=orbit)
            items.append((name, path))

        lab.sheet(items, OUT / "_hoja.png", cols=min(4, max(1, len(items))))
        browser.close()


if __name__ == "__main__":
    main()
