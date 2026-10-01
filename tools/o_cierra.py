"""Afina el contacto de la O con la palma hacia la camara (muneca y = -70)."""
import itertools
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

import search_e9
from o_circulo import MEDIR_JS, evaluar_lote, linea, pose, puntuar

search_e9.URL = "http://127.0.0.1:8124/practica.html?letra=O&v=ocierra"
OUT = Path(__file__).resolve().parents[1] / "tools" / "screenshots" / "o_circulo" / "cierra"

IDX = dict(icurl=0.64, i1=24, i2=6, i3=-10, ispread=4)


def candidatos():
    out = []
    for tcurl, aside, t1y, t1z, t2x, t3x in itertools.product(
        (0.22, 0.38, 0.55),
        (-0.55, -0.3, -0.05),
        (-50, -28, -8),
        (40, 62, 82),
        (35, 55, 75),
        (40, 60, 80),
    ):
        out.append(pose(
            tcurl=tcurl, aside=aside, t1x=-8, t1y=t1y, t1z=t1z,
            t2x=t2x, t3x=t3x, muneca={"y": -70}, cerrar=1.0, **IDX,
        ))
    return out


def disparar(page, viewer, nombre, pz):
    page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pz)
    time.sleep(0.2)
    m = page.evaluate(MEDIR_JS, pz)
    print(linea(nombre, m, puntuar(m)))
    h = page.evaluate(
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
          const e = B.RightHandIndex3.matrixWorld.elements;
          const off = (s.target && s.target.position) || {x:0,y:0,z:0};
          return { x: e[12]-off.x, y: e[13]-off.y, z: e[14]-off.z };
        }"""
    )
    t = "%.3fm %.3fm %.3fm" % (h["x"], h["y"], h["z"])
    for vista, orbit, fov in (
        ("app", "0deg 78deg 0.52m", "30deg"),
        ("cerca", "0deg 72deg 0.32m", "18deg"),
    ):
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
        time.sleep(0.28)
        viewer.screenshot(path=str(OUT / f"{nombre}_{vista}.png"))
    (OUT / f"{nombre}.json").write_text(json.dumps(pz, indent=2), encoding="utf-8")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    poses = candidatos()
    print("n", len(poses))
    with sync_playwright() as p:
        browser, page = search_e9.abrir(p)
        page.set_default_timeout(180000)
        page.set_viewport_size({"width": 700, "height": 700})
        viewer = page.query_selector("#handViewer")
        med = evaluar_lote(page, poses)
        rank = sorted(zip(poses, med), key=lambda it: puntuar(it[1]))
        print("top:")
        for pz, m in rank[:8]:
            t = pz["thumb"]
            e = pz["extra"]
            print(linea(
                f"c{t['curl']}_a{t['aside']}_y{e['RightHandThumb1']['y']}"
                f"_z{e['RightHandThumb1']['z']}_2{e['RightHandThumb2']['x']}_3{e['RightHandThumb3']['x']}",
                m, puntuar(m),
            ))
        for i, (pz, _m) in enumerate(rank[:4], start=1):
            disparar(page, viewer, f"{i:02d}", pz)
        browser.close()


if __name__ == "__main__":
    main()
