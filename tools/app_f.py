"""La F al tamano y con la camara de la pagina, antes y despues.

Reproduce lo que hace practica.html al pulsar la letra: la orbita declarada en el
catalogo (rig.cameraOrbit) y el punto de mira que calcula el propio controlador
siguiendo la mano. Sirve para juzgar si los tres dedos juntos se siguen leyendo
como tres a la distancia a la que se ve la seña, no solo en un primer plano.
"""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

import search_e9
from lab_e2 import hoja
from tres_f import TRES_JS
from verifica_f2 import ANTES

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "app_f"

# La camara de la portada (index.html, el visor del heroe): es la vista a la que
# mira la persona, mas lejos que el primer plano de practica.html. Se copia aqui
# porque el controlador de la portada vive dentro de una funcion anonima y no se
# le puede pedir una letra concreta.
# practica.html puede lanzar la carga del modelo dos veces (pone el src y, si el
# visor ya estaba cargado, dispara un 'load' a mano). La segunda vez el
# controlador ya tiene `restApplied` en true, asi que se salta las correcciones de
# reposo y el avatar se queda en la T del rig, con el brazo en cruz. En la pagina
# de la persona eso no pasa. Aqui se rehacen las correcciones sobre el esqueleto y
# se vuelve a capturar el reposo, para fotografiar la letra con el brazo levantado.
ENDEREZA_JS = """
() => {
  const mv = document.getElementById('handViewer');
  let s = null;
  for (const sym of Object.getOwnPropertySymbols(mv)) {
    const v = mv[sym];
    if (v && typeof v.traverse === 'function') { s = v; break; }
    if (v && v.model && typeof v.model.traverse === 'function') { s = v.model; break; }
    if (v && v.target && typeof v.target.traverse === 'function') { s = v.target; break; }
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
  window.__LSM_CONTROLLER__.refreshSkeleton();   // recaptura el reposo ya corregido
  return hechas;
}
"""

CAMARA_APP = """
() => {
  const mv = document.getElementById('handViewer');
  mv.cameraTarget = '-0.07m 1.42m 0.10m';
  mv.cameraOrbit = '0deg 84deg 1.55m';
  mv.fieldOfView = '30deg';
  mv.jumpCameraToGoal();
  return { orbita: mv.cameraOrbit, mira: mv.cameraTarget };
}
"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    fichas = []
    with sync_playwright() as p:
        search_e9.URL = "http://127.0.0.1:8006/practica.html?letra=F&v=appf2"
        browser, page = search_e9.abrir(p)
        # el visor de la pagina es panoramico; con el cuadrado de las pruebas la
        # mano sale a otra escala y no valdria para juzgar el encuadre real
        page.set_viewport_size({"width": 1180, "height": 820})
        time.sleep(1.2)
        print("correcciones de reposo rehechas:", page.evaluate(ENDEREZA_JS))
        viewer = page.query_selector("#viewer")

        for nombre, aplicar in (
            ("1_antes", lambda: page.evaluate(
                "(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", ANTES)),
            ("2_despues", lambda: page.evaluate(
                "() => window.__LSM_CONTROLLER__.mostrarSena('F', { loop: false })")),
        ):
            aplicar()
            time.sleep(3.6)
            cam = page.evaluate(CAMARA_APP)
            time.sleep(0.4)
            m = page.evaluate(TRES_JS)
            destino = OUT / f"{nombre}.png"
            viewer.screenshot(path=str(destino))
            fichas.append((nombre, destino))
            print(f"{nombre}: camara {cam['orbita']} mirando {cam['mira']} · "
                  f"pinza={m['pinza']:.3f}")
        browser.close()

    print("hoja:", hoja(fichas, OUT / "_app.png", cols=2, cell=560))


if __name__ == "__main__":
    main()
