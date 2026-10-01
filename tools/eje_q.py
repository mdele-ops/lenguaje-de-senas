"""Q: cuanto se mueve la mano en pantalla por cada grado de hombro/antebrazo.

La flecha de la lamina no es un giro de muneca: su centro cae justo debajo del
pico, a unos 0.44 largos de palma de las yemas, mientras que la muneca esta a
mas de 1.5 palmas. O sea, la mano ENTERA se traslada dibujando un circulo
pequeno, en sentido horario visto de frente.

Para montar ese circulo con keyframes hace falta saber cuanto desplaza la mano
cada grado de cada hueso del brazo. Aqui se mide esa relacion (el jacobiano) y
se resuelven los grados que hacen falta para un radio de 0.44 palmas.
"""
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from pose_lab_e import ARM, _GET_SCENE
from pose_lab_q import pose_q
import search_e9 as se9
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "eje_q.json"

se9.URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=ejeq"

FOREARM = "mixamorig1RightForeArm_034"
BASE = dict(wx=135, wz=45, idx_dip=45, tcurl=0.3, taside=0.3, t1y=-40, t1z=-20)
RADIO = 0.44  # largos de palma, medido sobre la flecha de la lamina

POS_JS = (
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
    const e = B[n].matrixWorld.elements;
    return { x: e[12], y: e[13], z: e[14] };
  };
  const w = P('mixamorig1RightHand_035');
  const i1 = P('mixamorig1RightHandIndex1_040');
  const i4 = P('mixamorig1RightHandIndex4_043');
  const t4 = P('mixamorig1RightHandThumb4_039');
  const palm = Math.hypot(w.x-i1.x, w.y-i1.y, w.z-i1.z) || 1;
  // el pico: punto medio entre las dos yemas, que es lo que dibuja el circulo
  return {
    palm: palm,
    picoX: (i4.x + t4.x) / 2, picoY: (i4.y + t4.y) / 2, picoZ: (i4.z + t4.z) / 2,
    wristX: w.x, wristY: w.y, wristZ: w.z,
  };
}
"""
)

EJES = [
    (ARM, "y", 8),
    (ARM, "z", 8),
    (ARM, "x", 8),
    (FOREARM, "x", 8),
    (FOREARM, "y", 8),
    (FOREARM, "z", 8),
]


def con(hueso, eje, grados, arm_z=-18):
    extra = {"z": arm_z}
    pose = pose_q(arm_z=arm_z, **BASE)
    if hueso == ARM:
        extra[eje] = extra.get(eje, 0) + grados
        pose["extra"][ARM] = extra
    else:
        pose["extra"][hueso] = {eje: grados}
    return pose


def main():
    with sync_playwright() as p:
        browser, page = abrir(p)
        time.sleep(0.3)

        page.evaluate(
            "(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose_q(**BASE)
        )
        time.sleep(0.3)
        base = page.evaluate(POS_JS)
        palm = base["palm"]
        print(f"palma = {palm:.4f} unidades; radio buscado = {RADIO * palm:.4f}")
        print(f"{'hueso':34s} {'eje':4s} {'dx/grado':>10s} {'dy/grado':>10s} {'dz/grado':>10s}")

        jac = {}
        for hueso, eje, paso in EJES:
            page.evaluate(
                "(x) => window.__LSM_CONTROLLER__.applyTestPose(x)",
                con(hueso, eje, paso),
            )
            time.sleep(0.2)
            m = page.evaluate(POS_JS)
            dx = (m["picoX"] - base["picoX"]) / paso / palm
            dy = (m["picoY"] - base["picoY"]) / paso / palm
            dz = (m["picoZ"] - base["picoZ"]) / paso / palm
            jac[f"{hueso}.{eje}"] = {"dx": dx, "dy": dy, "dz": dz}
            print(f"{hueso.replace('mixamorig1Right',''):34s} {eje:4s} "
                  f"{dx:+10.4f} {dy:+10.4f} {dz:+10.4f}")

        browser.close()

    OUT.write_text(json.dumps({"palm": palm, "radio": RADIO, "jac": jac}, indent=2), "utf-8")
    print("->", OUT)


if __name__ == "__main__":
    main()
