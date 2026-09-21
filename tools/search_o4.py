"""O, paso 4: con los dedos ya compactos, buscar a fondo el pulgar que cierra.

Los dedos quedan fijos en el arco compacto que salio del paso 3 (reach ~0.9,
dedos pegados) y se recorre un rango amplio del pulgar hasta que su yema toca
la del indice, que es lo que forma la O de la referencia.
"""
import json

from playwright.sync_api import sync_playwright

import lsm_lab as L

OUT = L.out_dir("search_o4")

# Arco compacto de dedos elegido en el paso 3.
FINGERS_FIXED = {"conv": -27, "c": 0.60, "k": 28, "m2": -10, "d3": -34}

AXES = {
    "tcurl": [0.30, 0.45, 0.60, 0.75, 0.90],
    "taside": [0.0, 0.25, 0.50, 0.75, 1.00],
    "t1y": [-40, -15, 10, 35, 60],
    "t1z": [0, 15, 30, 45, 60],
    "t2x": [-55, -35, -15, 5],
    "t3x": [-30, -10, 10, 30],
}

TARGET = {"dI": 0.05, "dM": 0.15, "dR": 0.30, "dP": 0.45}
WEIGHT = {"dI": 1.5, "dM": 0.6, "dR": 0.3, "dP": 0.15}


def score(m):
    return sum(WEIGHT[k] * abs(m[k] - TARGET[k]) for k in TARGET)


def fmt(m):
    return (
        f"dI={m['dI']:.2f} dM={m['dM']:.2f} dR={m['dR']:.2f} dP={m['dP']:.2f} "
        f"reach={m['reach']:.2f} hole={m['hole']:.2f}"
    )


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", args=L.CHROME_ARGS)
        page = L.open_ready_page(browser)

        res = L.grid_search(page, AXES, fixed=FINGERS_FIXED)
        print("combinaciones evaluadas:", len(res))
        for r in res:
            r["score"] = score(r["m"])
        res.sort(key=lambda r: r["score"])

        print("\n== top 14 ==")
        for r in res[:14]:
            print(f"s={r['score']:.3f} {fmt(r['m'])}")
            print(f"          {({k: r['p'][k] for k in AXES})}")

        (OUT / "ranking.json").write_text(
            json.dumps(res[:80], indent=2), encoding="utf-8"
        )

        viewer = page.query_selector("#viewer")
        for i, r in enumerate(res[:10]):
            L.apply_pose(page, L.pose_from_params(r["p"]))
            L.set_camera(page, orbit="-40deg 82deg 0.40m", fov="24deg")
            viewer.screenshot(path=str(OUT / f"top{i:02d}_s{r['score']:.3f}.png"))

        browser.close()
        print("->", OUT)


if __name__ == "__main__":
    main()
