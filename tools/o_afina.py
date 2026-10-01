"""Primeros planos de la O para cerrar el circulo y meter los tres dedos."""
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

import search_e9
from o_circulo import MEDIR_JS, OUT, linea, pose, puntuar

search_e9.URL = "http://127.0.0.1:8124/practica.html?letra=O&v=oafina2"
CERCA = OUT / "cerca"

# La forma que ya junta las yemas (fase pulgar, segunda).
BASE = dict(icurl=0.68, i1=32, i2=0, i3=-18, ispread=0,
            tcurl=0.30, aside=-0.3, t1x=-10, t1y=-30, t1z=65, t2x=55, t3x=55)


def variantes():
    v = []
    # la que se veia bien en la camara de la app, sin el giro de 70
    v.append(("a_base", pose(muneca=None, **BASE)))
    # puno mas cerrado: los tres dedos no deben asomar
    v.append(("b_puno", pose(muneca=None, cerrar=1.0, **BASE)))
    # arco del indice mas parejo, para que el agujero sea redondo
    v.append(("c_arco", pose(
        0.58, 18, 14, 8, 6,
        0.40, -0.25, -8, -20, 50, 40, 48,
        None, cerrar=1.0,
    )))
    v.append(("d_pinza", pose(
        0.62, 22, 8, -6, 4,
        0.45, -0.2, -12, -15, 40, 35, 62,
        None, cerrar=1.0,
    )))
    v.append(("e_pulgar", pose(
        0.62, 22, 8, -6, 4,
        0.55, -0.45, 8, -40, 55, 28, 40,
        None, cerrar=1.0,
    )))
    v.append(("f_junto", pose(
        0.5, 10, 18, 12, 2,
        0.5, -0.15, -5, 5, 35, 30, 45,
        None, cerrar=1.0,
    )))
    return v


def mira(page):
    return page.evaluate(
        """() => {
          const mv = document.getElementById('handViewer');
          let s = null;
          for (const sym of Object.getOwnPropertySymbols(mv)) {
            const v = mv[sym];
            if (v && typeof v.traverse === 'function') { s = v; break; }
          }
          s.updateMatrixWorld(true);
          const B = {};
          s.traverse((o) => { if (o && o.name) B[o.name] = o; });
          const P = (n) => B[n].matrixWorld.elements;
          const a = P('RightHandIndex2'), b = P('RightHandThumb2');
          const off = (s.target && s.target.position) || { x: 0, y: 0, z: 0 };
          return {
            x: (a[12] + b[12]) / 2 - off.x,
            y: (a[13] + b[13]) / 2 - off.y,
            z: (a[14] + b[14]) / 2 - off.z,
          };
        }"""
    )


def main():
    CERCA.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser, page = search_e9.abrir(p)
        page.set_viewport_size({"width": 720, "height": 720})
        viewer = page.query_selector("#handViewer")
        for nombre, pz in variantes():
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pz)
            time.sleep(0.3)
            m = page.evaluate(MEDIR_JS, pz)
            print(linea(nombre, m, puntuar(m)))
            h = mira(page)
            t = "%.3fm %.3fm %.3fm" % (h["x"], h["y"], h["z"])
            for vista, orbit, fov in (
                ("app", "0deg 78deg 0.52m", "30deg"),
                ("cerca", "12deg 68deg 0.30m", "18deg"),
                ("lado", "-40deg 72deg 0.30m", "18deg"),
            ):
                for _ in range(2):
                    page.evaluate(
                        """(a) => {
                            const mv = document.getElementById('handViewer');
                            mv.minCameraOrbit = 'auto 0deg 0.05m';
                            mv.maxCameraOrbit = 'auto 180deg 10m';
                            mv.cameraTarget = a.t;
                            mv.cameraOrbit = a.o;
                            mv.fieldOfView = a.f;
                            mv.jumpCameraToGoal();
                        }""",
                        {"t": t, "o": orbit, "f": fov},
                    )
                    time.sleep(0.2)
                viewer.screenshot(path=str(CERCA / f"{nombre}_{vista}.png"))
            (CERCA / f"{nombre}.json").write_text(
                json.dumps(pz, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        browser.close()


if __name__ == "__main__":
    main()
