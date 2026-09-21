"""P lab 7: poner la mano de perfil para que los dos dedos se vean completos.

Con el giro de 45 la letra se forma bien pero se ve de tres cuartos: se ve
media palma y el dedo medio, que apunta en diagonal hacia la camara, sale
corto. En la lamina los dos dedos se ven a su largo completo, y eso solo pasa
si el plano que forman indice y medio queda paralelo a la pantalla.

El dedo medio doblado 90 en el nudillo apunta justo en la direccion de la
NORMAL de la palma. Asi que la condicion es: normal de la palma hacia el
costado (eje x), nunca hacia la camara (eje z). Se mide:

  palmNx  componente x de la normal de la palma (queremos ~+1)
  palmNz  componente z (queremos ~0: si crece, se ve la palma de frente)
  midSide el medio apuntando al costado en pantalla (queremos ~+1)

Las capturas se toman con la camara REAL de practica.html y luego se recortan,
para juzgar exactamente lo que ve el usuario y no un encuadre inventado.
"""
import json
import time
from pathlib import Path

from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright

from pose_lab_e import ARM, BONES, _GET_SCENE
from pose_lab_p import REF
import search_e9 as se9
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "lab_p7"
OUT.mkdir(parents=True, exist_ok=True)

se9.URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=p7"

FOREARM = "mixamorig1RightForeArm_034"
T1 = "mixamorig1RightHandThumb1_036"
T2 = "mixamorig1RightHandThumb2_037"

# Camara de produccion tal cual la define el catalogo.
CAM_TARGET = "0m 2.45m 0.15m"
CAM_ORBIT = "0deg 84deg 2.5m"
CAM_FOV = "30deg"

MEASURE_JS = (
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
    if (!b || !b.matrixWorld) return null;
    const e = b.matrixWorld.elements;
    return { x: e[12], y: e[13], z: e[14] };
  };
  const sub = (a, b) => ({ x: a.x-b.x, y: a.y-b.y, z: a.z-b.z });
  const norm = (v) => {
    const l = Math.hypot(v.x, v.y, v.z) || 1;
    return { x: v.x/l, y: v.y/l, z: v.z/l };
  };
  const cross = (a, b) => ({
    x: a.y*b.z - a.z*b.y,
    y: a.z*b.x - a.x*b.z,
    z: a.x*b.y - a.y*b.x,
  });
  const d = (a, b) => Math.hypot(a.x-b.x, a.y-b.y, a.z-b.z);

  const wrist = P('mixamorig1RightHand_035');
  const i1 = P('mixamorig1RightHandIndex1_040');
  const i4 = P('mixamorig1RightHandIndex4_043');
  const m1 = P('mixamorig1RightHandMiddle1_044');
  const m4 = P('mixamorig1RightHandMiddle4_047');
  const p1 = P('mixamorig1RightHandPinky1_052');
  const palm = d(wrist, i1) || 1;

  // normal de la palma: nudillos (indice->menique) x eje de la palma
  const nrm = norm(cross(sub(p1, i1), sub(m1, wrist)));
  const index = norm(sub(i4, i1));
  const middle = norm(sub(m4, m1));
  const dot = index.x*middle.x + index.y*middle.y + index.z*middle.z;

  return {
    palmNx: nrm.x, palmNy: nrm.y, palmNz: nrm.z,
    idxUp: index.y, idxFwd: index.z,
    midSide: middle.x, midUp: middle.y, midFwd: middle.z,
    escuadra: Math.acos(Math.max(-1, Math.min(1, dot))) * 180 / Math.PI,
    // largo aparente de cada dedo proyectado en la pantalla (plano x-y):
    // es lo que hace que el dedo "se vea completo" o salga corto
    idxScr: Math.hypot(i4.x-i1.x, i4.y-i1.y) / palm,
    midScr: Math.hypot(m4.x-m1.x, m4.y-m1.y) / palm,
  };
}
"""
)


def pose_p7(wy=45, wz=12, wx=0, fore=None, tcurl=0.75, taside=-0.3, t1y=-85, t2x=25,
            mid_mcp=90, arm_z=-18, arm=None):
    ex = {
        BONES["middle"][0]: {"x": mid_mcp},
        T1: {"y": t1y},
        T2: {"x": t2x},
    }
    ex[ARM] = dict({"z": arm_z}, **(arm or {}))
    if fore:
        ex[FOREARM] = dict(fore)
    muneca = {k: v for k, v in (("x", wx), ("y", wy), ("z", wz)) if v}
    pose = {
        "thumb": {"curl": tcurl, "aside": taside},
        "index": {"curl": 0.0, "spread": 4},
        "middle": {"curl": 0.0, "spread": -4},
        "ring": {"curl": 0.95},
        "pinky": {"curl": 0.95},
        "extra": ex,
    }
    if muneca:
        pose["muneca"] = muneca
    return pose


CASES = {
    "00_actual45": pose_p7(wy=45),
    # solo muñeca, cada vez mas girada
    "A_wy65": pose_p7(wy=65),
    "B_wy80": pose_p7(wy=80),
    "C_wy95": pose_p7(wy=95),
    # el giro repartido: el antebrazo prona y la muñeca acompaña (natural)
    "D_fore_y40": pose_p7(wy=45, fore={"y": 40}),
    "E_fore_x40": pose_p7(wy=45, fore={"x": 40}),
    "F_fore_z40": pose_p7(wy=45, fore={"z": 40}),
    "G_fore_y-40": pose_p7(wy=45, fore={"y": -40}),
    "H_fore_x-40": pose_p7(wy=45, fore={"x": -40}),
    "I_fore_z-40": pose_p7(wy=45, fore={"z": -40}),
}


def hoja(items, out_path, cols=4, cell=320, caja=None):
    lh = 24
    filas = (len(items) + cols - 1) // cols
    canvas = Image.new("RGB", (cols * cell, filas * (cell + lh)), (245, 245, 248))
    draw = ImageDraw.Draw(canvas)
    for i, (name, path) in enumerate(items):
        x, y = (i % cols) * cell, (i // cols) * (cell + lh)
        im = Image.open(path).convert("RGB")
        if caja and "REF" not in name:
            im = im.crop(caja)
        lado = min(im.size)
        im = im.crop(
            (
                (im.width - lado) // 2,
                (im.height - lado) // 2,
                (im.width + lado) // 2,
                (im.height + lado) // 2,
            )
        )
        canvas.paste(im.resize((cell, cell), Image.LANCZOS), (x, y))
        draw.rectangle([x, y + cell, x + cell, y + cell + lh], fill=(20, 30, 50))
        draw.text((x + 6, y + cell + 7), name, fill=(255, 255, 255))
    canvas.save(out_path)
    print("Hoja:", out_path)


def main():
    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 1100, "height": 900})
        time.sleep(0.5)
        viewer = page.query_selector("#viewer")
        page.evaluate(
            """(a) => {
                const mv = document.getElementById('handViewer');
                mv.cameraTarget = a.t;
                mv.cameraOrbit = a.orbit;
                mv.fieldOfView = a.fov;
                mv.jumpCameraToGoal();
            }""",
            {"t": CAM_TARGET, "orbit": CAM_ORBIT, "fov": CAM_FOV},
        )
        time.sleep(0.4)

        items = [("REF lamina", REF)] if REF.exists() else []
        for name, pose in CASES.items():
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
            time.sleep(0.35)
            m = page.evaluate(MEASURE_JS)
            print(
                f"{name:12s} palmN=({m['palmNx']:+.2f},{m['palmNz']:+.2f}) "
                f"midSide={m['midSide']:+.2f} midFwd={m['midFwd']:+.2f} "
                f"ang={m['escuadra']:5.1f} largoPantalla idx={m['idxScr']:.2f} "
                f"mid={m['midScr']:.2f}"
            )
            path = OUT / f"{name}.png"
            viewer.screenshot(path=str(path))
            items.append((name, path))

        browser.close()

    # la mano cae siempre en la misma zona del cuadro de produccion
    hoja(items, OUT / "_produccion.png", cols=4, cell=330, caja=(210, 60, 470, 320))
    (OUT / "_casos.json").write_text(json.dumps(CASES, indent=2), "utf-8")


if __name__ == "__main__":
    main()
