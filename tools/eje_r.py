"""R lab 2: hacia donde mira la palma y como encuadrar una mano con los dedos
arriba.

Dos cosas que hay que dejar claras antes de buscar el cruce:

  1. En la lamina la R se ve con la palma AL FRENTE (se asoman las unas de los
     dedos recogidos). Hay que comprobar si la camara de produccion ve la palma
     o el dorso, porque de eso depende cual de los dos dedos tiene que pasar
     por delante para que el cruce se lea.
  2. El encuadre de los otros labs centra la camara entre muneca y nudillo, que
     sirve para letras de puno; con la R los dedos suben casi un palmo por
     encima y se salen del cuadro. Aqui el objetivo se calcula sobre la yema
     mas alta.
"""
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from pose_lab_e import _GET_SCENE, free_camera
import search_e9 as se9
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "eje_r"
OUT.mkdir(parents=True, exist_ok=True)

se9.URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=r2"

CAM_TARGET = "0m 2.45m 0.15m"
CAM_ORBIT = "0deg 84deg 2.5m"
CAM_FOV = "30deg"

# Orientacion de la palma en el sistema de la CAMARA, no del mundo: es lo unico
# que dice si el espectador ve la palma o el dorso.
ORIENT_JS = (
    """
() => {
  const mv = document.getElementById('handViewer');
"""
    + _GET_SCENE
    + """
  const scene = getScene(mv);
  if (!scene) return { error: 'no-scene' };
  scene.updateMatrixWorld(true);
  const B = {};
  scene.traverse((o) => { if (o && o.name) B[o.name] = o; });
  const P = (n) => {
    const b = B[n];
    if (!b) return null;
    const e = b.matrixWorld.elements;
    return { x: e[12], y: e[13], z: e[14] };
  };
  const sub = (a, b) => ({ x: a.x-b.x, y: a.y-b.y, z: a.z-b.z });
  const dot = (a, b) => a.x*b.x + a.y*b.y + a.z*b.z;
  const cross = (a, b) => ({
    x: a.y*b.z - a.z*b.y, y: a.z*b.x - a.x*b.z, z: a.x*b.y - a.y*b.x,
  });
  const norm = (v) => {
    const l = Math.hypot(v.x, v.y, v.z) || 1;
    return { x: v.x/l, y: v.y/l, z: v.z/l };
  };

  const wrist = P('mixamorig1RightHand_035');
  const kI = P('mixamorig1RightHandIndex1_040');
  const kP = P('mixamorig1RightHandPinky1_052');
  const kM = P('mixamorig1RightHandMiddle1_044');
  const t4 = P('mixamorig1RightHandThumb4_039');

  // misma normal que usan los demas labs
  const nrm = norm(cross(sub(kP, kI), sub(kM, wrist)));

  // camara: model-viewer expone getCameraOrbit/getCameraTarget en metros
  const orb = mv.getCameraOrbit();
  const tgt = mv.getCameraTarget();
  const cam = {
    x: tgt.x + orb.radius * Math.sin(orb.phi) * Math.sin(orb.theta),
    y: tgt.y + orb.radius * Math.cos(orb.phi),
    z: tgt.z + orb.radius * Math.sin(orb.phi) * Math.cos(orb.theta),
  };
  // el modelo se traslada por -cameraTarget; las posiciones de hueso ya salen
  // en ese sistema, asi que hay que llevar la camara al mismo sitio
  const off = (scene.target && scene.target.position) || { x: 0, y: 0, z: 0 };
  const camL = { x: cam.x + off.x, y: cam.y + off.y, z: cam.z + off.z };

  const haciaCam = norm(sub(camL, wrist));
  // eje derecha de la pantalla, para saber de que lado sale el pulgar
  const der = norm(cross({ x: 0, y: 1, z: 0 }, sub(wrist, camL)));

  return {
    nrmHaciaCam: dot(nrm, haciaCam),   // >0 = la normal apunta al espectador
    pulgarDer: dot(norm(sub(t4, wrist)), der),  // >0 = pulgar a la derecha
    indiceDer: dot(norm(sub(kI, wrist)), der),
    meniqueDer: dot(norm(sub(kP, wrist)), der),
  };
}
"""
)

# Encuadre para manos con los dedos hacia arriba: el objetivo se pone entre la
# muneca y la yema mas alta, no en el centro del puno.
HAND_UP_JS = (
    """
() => {
  const mv = document.getElementById('handViewer');
"""
    + _GET_SCENE
    + """
  const scene = getScene(mv);
  scene.updateMatrixWorld(true);
  const B = {};
  scene.traverse((o) => { if (o && o.name) B[o.name] = o; });
  const P = (n) => {
    const b = B[n];
    if (!b) return null;
    const e = b.matrixWorld.elements;
    return { x: e[12], y: e[13], z: e[14] };
  };
  const wrist = P('mixamorig1RightHand_035');
  const tips = [
    'mixamorig1RightHandIndex4_043', 'mixamorig1RightHandMiddle4_047',
    'mixamorig1RightHandRing4_051', 'mixamorig1RightHandPinky4_055',
    'mixamorig1RightHandThumb4_039',
  ].map(P);
  let alto = wrist;
  tips.forEach((t) => { if (t && t.y > alto.y) alto = t; });
  const off = (scene.target && scene.target.position) || { x: 0, y: 0, z: 0 };
  return {
    x: (wrist.x + alto.x) / 2 - off.x,
    y: (wrist.y + alto.y) / 2 - off.y,
    z: (wrist.z + alto.z) / 2 - off.z,
    alcance: Math.hypot(alto.x - wrist.x, alto.y - wrist.y, alto.z - wrist.z),
  };
}
"""
)


def cam(page, target, orbit, fov):
    page.evaluate(
        """(a) => {
            const mv = document.getElementById('handViewer');
            mv.cameraTarget = a.t;
            mv.cameraOrbit = a.orbit;
            mv.fieldOfView = a.fov;
            mv.jumpCameraToGoal();
        }""",
        {"t": target, "orbit": orbit, "fov": fov},
    )
    time.sleep(0.22)


def encuadrar(page, orbit_deg=0, holgura=2.6):
    """Centra en la mano y ajusta el radio al alcance real dedos-muneca."""
    h = page.evaluate(HAND_UP_JS)
    radio = max(0.35, h["alcance"] * holgura)
    cam(
        page,
        "%.3fm %.3fm %.3fm" % (h["x"], h["y"], h["z"]),
        f"{orbit_deg}deg 84deg {radio:.3f}m",
        "26deg",
    )
    return h


def main():
    catalogo = json.loads((ROOT / "data" / "catalogo-lsm.json").read_text("utf-8"))
    por_letra = {s["letra"]: s for s in catalogo["senas"]}

    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 900, "height": 900})
        time.sleep(0.4)
        viewer = page.query_selector("#viewer")
        free_camera(page)

        for letra in ("B", "U", "R"):
            pose = por_letra[letra]["pose"]
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
            time.sleep(0.3)

            cam(page, CAM_TARGET, CAM_ORBIT, CAM_FOV)
            o = page.evaluate(ORIENT_JS)
            print(
                f"{letra}: normal->camara={o['nrmHaciaCam']:+.2f}  "
                f"pulgar a la derecha={o['pulgarDer']:+.2f}  "
                f"indice={o['indiceDer']:+.2f}  menique={o['meniqueDer']:+.2f}"
            )
            viewer.screenshot(path=str(OUT / f"{letra}_produccion.png"))

            for nombre, grados in (("frente", 0), ("lado", -70)):
                encuadrar(page, grados)
                viewer.screenshot(path=str(OUT / f"{letra}_{nombre}.png"))

        browser.close()

    print("\nnormal->camara > 0 significa que el espectador ve el DORSO,")
    print("porque la normal de estos labs sale por el dorso de la mano.")
    print("Capturas en", OUT)


if __name__ == "__main__":
    main()
