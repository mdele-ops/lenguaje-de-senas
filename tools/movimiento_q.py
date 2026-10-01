"""Q: el trazo. La mano, sin cambiar de forma, dibuja el redondel de la letra.

De eje_q.py salen los dos huesos que mueven la mano en el plano de la pantalla
casi sin mezclarse:

    hombro x    -> horizontal
    antebrazo x -> vertical

Con esas dos derivadas se resuelve, para cada punto del circulo, cuantos grados
necesita cada hueso. El resultado son los keyframes del ciclo del catalogo.

Ojo con como interpola el controlador: sampleCyclePose mezcla `muneca` y cada
hueso de `extra` con lerpXYZ, que rellena con CERO los ejes que falten. Por eso
cada keyframe repite la muneca y el `z` del hombro completos: si no, la mano
perderia el giro de la letra a mitad del trazo.
"""
import json
import math
import time
from pathlib import Path

from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright

from pose_lab_e import ARM, _GET_SCENE, free_camera
from pose_lab_p7 import CAM_FOV, CAM_ORBIT, CAM_TARGET, hoja
from pose_lab_q import pose_q
from pose_lab_q2 import cam
import search_e9 as se9
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "lab_q_mov"
OUT.mkdir(parents=True, exist_ok=True)
JAC = ROOT / "tools" / "screenshots" / "eje_q.json"

se9.URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=qmov"

FOREARM = "mixamorig1RightForeArm_034"
WRIST = {"x": 135, "y": 0, "z": 45}
ARM_Z = -18
BASE = dict(wx=WRIST["x"], wz=WRIST["z"], idx_dip=45,
            tcurl=0.3, taside=0.3, t1y=-40, t1z=-20, arm_z=ARM_Z)

# La flecha de la lamina arranca arriba y gira en sentido horario visto de
# frente, cerrando casi el circulo completo.
ANG0 = 100.0
PASOS = 12
RADIO = 0.44

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
  return { palm: palm, x: (i4.x+t4.x)/2, y: (i4.y+t4.y)/2, z: (i4.z+t4.z)/2 };
}
"""
)


def grados(jac, dx, dy):
    """Grados de hombro-x y antebrazo-x para desplazar el pico (dx, dy)."""
    a = jac["mixamorig1RightArm_033.x"]
    f = jac["mixamorig1RightForeArm_034.x"]
    det = a["dx"] * f["dy"] - f["dx"] * a["dy"]
    ga = (f["dy"] * dx - f["dx"] * dy) / det
    gf = (-a["dy"] * dx + a["dx"] * dy) / det
    return ga, gf


def keyframes(jac, pasos=PASOS, radio=RADIO, ang0=ANG0):
    kfs = []
    for i in range(pasos + 1):
        ang = math.radians(ang0 - 360.0 * i / pasos)
        ga, gf = grados(jac, radio * math.cos(ang), radio * math.sin(ang))
        kfs.append(
            {
                "t": round(i / pasos, 4),
                "muneca": dict(WRIST),
                "extra": {
                    ARM: {"x": round(ga, 2), "z": ARM_Z},
                    FOREARM: {"x": round(gf, 2)},
                },
            }
        )
    return kfs


def pose_en(kf):
    pose = pose_q(**BASE)
    pose["muneca"] = dict(kf["muneca"])
    for hueso, rot in kf["extra"].items():
        pose["extra"][hueso] = dict(rot)
    return pose


def main():
    datos = json.loads(JAC.read_text("utf-8"))
    kfs = keyframes(datos["jac"])

    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 1100, "height": 900})
        time.sleep(0.4)
        viewer = page.query_selector("#viewer")
        free_camera(page)
        cam(page, CAM_TARGET, CAM_ORBIT, CAM_FOV)

        tiras, puntos = [], []
        for i, kf in enumerate(kfs[:-1]):
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose_en(kf))
            time.sleep(0.25)
            m = page.evaluate(POS_JS)
            puntos.append((m["x"] / m["palm"], m["y"] / m["palm"]))
            path = OUT / f"{i:02d}.png"
            viewer.screenshot(path=str(path))
            tiras.append((f"t={kf['t']}", path))

        browser.close()

    # el trazo real del pico, para cotejarlo con la flecha de la lamina
    xs = [q[0] for q in puntos]
    ys = [q[1] for q in puntos]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    print(f"ancho={max(xs)-min(xs):.3f} alto={max(ys)-min(ys):.3f} palmas "
          f"(objetivo {2*RADIO:.2f})")
    for i, (x, y) in enumerate(puntos):
        ang = math.degrees(math.atan2(y - cy, x - cx))
        r = math.hypot(x - cx, y - cy)
        print(f"  {i:2d} ang={ang:+7.1f} r={r:.3f}")

    lienzo = Image.new("RGB", (420, 420), (255, 255, 255))
    draw = ImageDraw.Draw(lienzo)
    esc = 170 / max(RADIO, 1e-6)
    pix = [(210 + (x - cx) * esc, 210 - (y - cy) * esc) for x, y in puntos]
    draw.line(pix + [pix[0]], fill=(150, 20, 60), width=5)
    for i, (px, py) in enumerate(pix):
        draw.ellipse([px - 5, py - 5, px + 5, py + 5], fill=(150, 20, 60))
        draw.text((px + 8, py - 6), str(i), fill=(40, 40, 40))
    lienzo.save(OUT / "_trazo.png")
    print("Trazo:", OUT / "_trazo.png")

    hoja(tiras, OUT / "_tira.png", cols=4, cell=320, caja=(150, 120, 480, 450))
    (OUT / "_keyframes.json").write_text(json.dumps(kfs, indent=2), "utf-8")


if __name__ == "__main__":
    main()
