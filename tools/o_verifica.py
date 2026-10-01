"""La O tal como la muestra el boton de practica, no una pose de prueba."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

import search_e9

search_e9.URL = "http://127.0.0.1:8124/practica.html?letra=O&v=overifica"
OUT = Path(__file__).resolve().parents[1] / "tools" / "screenshots" / "o_circulo"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser, page = search_e9.abrir(p)
        page.set_viewport_size({"width": 720, "height": 720})
        time.sleep(0.4)
        print("endereza", page.evaluate(
            """() => {
              const mv = document.getElementById('handViewer');
              let s = null;
              for (const sym of Object.getOwnPropertySymbols(mv)) {
                const v = mv[sym];
                if (v && typeof v.traverse === 'function') { s = v; break; }
              }
              const B = {};
              s.traverse((o) => { if (o && o.name) B[o.name] = o; });
              const rig = window.__LSM_CONTROLLER__.getCatalog().rig;
              const DEG = Math.PI / 180;
              let hechas = 0;
              (rig.restCorrections || []).forEach((item) => {
                const b = B[item.hueso];
                if (!b) return;
                (item.rotaciones || []).forEach(([eje, grados]) => {
                  if (eje === 'x') b.rotateX(grados * DEG);
                  else if (eje === 'y') b.rotateY(grados * DEG);
                  else b.rotateZ(grados * DEG);
                });
                hechas++;
              });
              window.__LSM_CONTROLLER__.refreshSkeleton();
              return hechas;
            }"""
        ))
        info = page.evaluate(
            """() => {
              const r = window.__LSM_CONTROLLER__.mostrarSena('O', { loop: false });
              const s = window.__LSM_CONTROLLER__.getSena('O');
              const mv = document.getElementById('handViewer');
              return {
                modo: r.modo,
                curl: s.pose.index.curl,
                medio: s.pose.middle.curl,
                y: s.pose.muneca.y,
                orbita: mv.cameraOrbit,
                mira: mv.cameraTarget,
              };
            }"""
        )
        print("antes", info)
        time.sleep(2.8)
        page.query_selector("#handViewer").screenshot(path=str(OUT / "final_pagina.png"))
        cam = page.evaluate(
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
              const P = (n) => {
                const e = B[n].matrixWorld.elements;
                return [e[12], e[13], e[14]];
              };
              return { mano: P('RightHand'), codo: P('RightForeArm'), orbita: mv.getCameraOrbit && String(mv.cameraOrbit), mira: mv.cameraTarget };
            }"""
        )
        print("cam", cam)
        browser.close()


if __name__ == "__main__":
    main()
