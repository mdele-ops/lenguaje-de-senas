"""La O con los cuatro dedos curvados sobre la punta del pulgar.

Uso: python _run.py o_redonda.py [candidatos.json]
Cada candidato es una pose completa; se captura el visor con la camara de la
aplicacion y de cerca, y se mide la distancia de la punta del pulgar a cada
yema, normalizada al largo de la palma (muneca -> nudillo del indice).
"""
import json
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from enfoque_r import hoja
import lupa_t
from lupa_t import cam, cam_app
from mira_t import abrir_nitido
from pose_lab_e import _GET_SCENE, free_camera
import search_e9 as se9

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "o_redonda"
se9.URL = "http://127.0.0.1:8124/practica.html?letra=O&v=oredonda"

MIDE_JS = (
    """
() => {
  const mv = document.getElementById('handViewer');
"""
    + _GET_SCENE
    + """
  const s = getScene(mv);
  s.updateMatrixWorld(true);
  const B = {};
  s.traverse((o) => {
    if (!o || !o.name) return;
    const m = o.name.match(/RightHand(Thumb|Index|Middle|Ring|Pinky)?(\\d)?(?:_\\d+)?$/);
    if (m) B['RightHand' + (m[1] || '') + (m[2] || '')] = o;
    if (/RightForeArm(?:_\\d+)?$/.test(o.name)) B.RightForeArm = o;
  });
  const P = (n) => { const e = B[n].matrixWorld.elements; return [e[12], e[13], e[14]]; };
  const d = (a, b) => Math.hypot(a[0]-b[0], a[1]-b[1], a[2]-b[2]);
  const palma = d(P('RightHand'), P('RightHandIndex1'));
  const t = P('RightHandThumb4');
  const r = {};
  for (const f of ['Index', 'Middle', 'Ring', 'Pinky']) {
    r[f] = +(d(t, P('RightHand' + f + '4')) / palma).toFixed(2);
  }
  const sub = (a, b) => [a[0]-b[0], a[1]-b[1], a[2]-b[2]];
  const ang = (u, v) => Math.acos((u[0]*v[0]+u[1]*v[1]+u[2]*v[2]) / (Math.hypot(...u) * Math.hypot(...v))) * 180 / Math.PI;
  const antebrazo = sub(P('RightHand'), P('RightForeArm'));
  const mano = sub(P('RightHandMiddle1'), P('RightHand'));
  r.doblez = Math.round(ang(antebrazo, mano));
  r.vertical = Math.round(ang(mano, [0, 1, 0]));
  r.brazoV = Math.round(ang(antebrazo, [0, 1, 0]));
  const m1 = P('RightHandMiddle1');
  const a = [(m1[0] + t[0]) / 2, (m1[1] + t[1]) / 2, (m1[2] + t[2]) / 2];
  const off = (s.target && s.target.position) || { x: 0, y: 0, z: 0 };
  r.centro = [a[0] - off.x, a[1] - off.y, a[2] - off.z];
  return r;
}
"""
)

lupa_t.FOV = "9deg"
VISTAS = (("frente", "0deg 84deg 1.05m"),)


SOLO_MIDE = "--mide" in sys.argv


def main():
    args = [a for a in sys.argv[1:] if a != "--mide"]
    cand_path = Path(args[0]) if args else OUT / "candidatos.json"
    candidatos = json.loads(cand_path.read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)
    items = []
    with sync_playwright() as p:
        browser, page = abrir_nitido(p, lado=600, escala=2)
        viewer = page.query_selector("#handViewer")
        app = page.evaluate(
            "() => { const mv = document.getElementById('handViewer');"
            " return { t: String(mv.cameraTarget), o: String(mv.cameraOrbit), f: String(mv.fieldOfView) }; }"
        )
        free_camera(page)
        for nombre, pose in candidatos.items():
            page.evaluate("(q) => window.__LSM_CONTROLLER__.applyTestPose(q)", pose)
            page.evaluate(
                "(a) => { const mv = document.getElementById('handViewer');"
                " mv.cameraTarget = a.t; mv.cameraOrbit = a.o; mv.fieldOfView = a.f;"
                " mv.jumpCameraToGoal(); }",
                app,
            )
            time.sleep(0.5)
            m = page.evaluate(MIDE_JS)
            centro = m.pop("centro")
            print(nombre, m)
            if SOLO_MIDE:
                continue
            ruta = OUT / f"{nombre}_app.png"
            viewer.screenshot(path=str(ruta))
            items.append((f"{nombre} app", ruta))
            for vista, orbit in VISTAS:
                cam(page, centro, orbit)
                ruta = OUT / f"{nombre}_{vista}.png"
                viewer.screenshot(path=str(ruta))
                items.append((f"{nombre} {vista}", ruta))
        browser.close()
    if SOLO_MIDE:
        return
    hoja(items, OUT / "_hoja.png", cols=3, cell=360, titulo="O redonda")


if __name__ == "__main__":
    main()
