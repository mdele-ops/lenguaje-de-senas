"""O, paso 3: rejilla amplia buscando el circulo compacto de la referencia.

Medida clave que faltaba: 'reach' (muneca -> yema del indice, normalizado al
largo de la palma). En la foto de referencia la yema del indice queda MAS CERCA
de la muneca que los nudillos (reach ~0.85), es decir la mano esta muy recogida;
la pose actual del catalogo tiene los dedos bastante estirados.
"""
import json

from playwright.sync_api import sync_playwright

import lsm_lab as L

OUT = L.out_dir("search_o3")

TARGET = {"dI": 0.05, "dM": 0.15, "dR": 0.30, "dP": 0.45, "reach": 0.85}
WEIGHT = {"dI": 1.2, "dM": 0.7, "dR": 0.4, "dP": 0.25, "reach": 1.0}
GAP_WEIGHT = 0.5

AXES = {
    "conv": [-34, -27, -20],
    "c": [0.40, 0.50, 0.60, 0.70],
    "k": [16, 28, 40],
    "m2": [-10, 8, 26],
    "d3": [-34, -18, -2],
    "tcurl": [0.30, 0.42, 0.54],
    "taside": [0.45, 0.62, 0.80],
    "t1z": [34, 44, 54],
    "t2x": [-14, -26, -38],
}


def score(m):
    s = sum(WEIGHT[k] * abs(m[k] - TARGET[k]) for k in TARGET)
    s += GAP_WEIGHT * (m["gIM"] + m["gMR"] + m["gRP"])
    return s


def fmt(m):
    return (
        f"dI={m['dI']:.2f} dM={m['dM']:.2f} dR={m['dR']:.2f} dP={m['dP']:.2f} "
        f"g={m['gIM']:.2f}/{m['gMR']:.2f}/{m['gRP']:.2f} "
        f"reach={m['reach']:.2f} hole={m['hole']:.2f}"
    )


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", args=L.CHROME_ARGS)
        page = L.open_ready_page(browser)

        # Referencia: como mide la pose que hay hoy en el catalogo
        page.evaluate(
            "() => { const c = window.__LSM_CONTROLLER__;"
            " c.applyTestPose(c.getSena('O').pose); }"
        )
        base = L.measure(page)
        print("catalogo actual :", fmt(base), f" score={score(base):.3f}")

        res = L.grid_search(page, AXES)
        print("combinaciones evaluadas:", len(res))
        for r in res:
            r["score"] = score(r["m"])
        res.sort(key=lambda r: r["score"])

        print("\n== top 12 ==")
        for r in res[:12]:
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
