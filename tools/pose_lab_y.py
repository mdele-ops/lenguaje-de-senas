"""Y lab 1: orientación de la muñeca.

La lámina pide palma al frente, pulgar arriba-izquierda y meñique casi
horizontal a la derecha (la Y / el teléfono). El catálogo actual deja la
Y como una I con el pulgar abierto: meñique hacia arriba, sin giro.
J enseña que muneca.z positivo engancha el meñique a la izquierda, así
que z negativo lo manda a la derecha. Se barre ese giro junto con un
poco de antebrazo para que la muñeca no se quiebre.
"""
import json
import shutil
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from eje_r import CAM_FOV, CAM_ORBIT, CAM_TARGET, cam
from enfoque_r import MANO, captura, hoja
from pose_lab_e import ARM, T1, T2, _GET_SCENE, free_camera
from pose_lab_x2 import FOREARM
from search_e9 import VISOR_CACHE
import search_e9 as se9

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "lab_y"
OUT.mkdir(parents=True, exist_ok=True)
CATALOGO = ROOT / "data" / "catalogo-lsm.json"
REF_SRC = Path(
    r"C:\Users\KZTRDG\.cursor\projects"
    r"\c-Users-KZTRDG-General-Motors-Christian-Osvaldo-Partida-Cadena-Becarios-Manu-Lenguaje-de-se-as"
    r"\assets"
    r"\c__Users_KZTRDG_AppData_Roaming_Cursor_User_workspaceStorage"
    r"_e58e5485bac69e9b6ccd69cb178bd5da_images_image-3bf05998-d8ec-4a68-acd4-e98e23919fd6.png"
)
REF = ROOT / "tools" / "screenshots" / "referencia" / "Y_usuario.png"

se9.URL = "http://127.0.0.1:8006/practica.html?letra=%E2%97%8B&v=y1"

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
    if (!b) return null;
    const e = b.matrixWorld.elements;
    return { x: e[12], y: e[13], z: e[14] };
  };
  const sub = (a, b) => ({ x: a.x-b.x, y: a.y-b.y, z: a.z-b.z });
  const dot = (a, b) => a.x*b.x + a.y*b.y + a.z*b.z;
  const nrm = (v) => {
    const l = Math.hypot(v.x, v.y, v.z) || 1;
    return { x: v.x/l, y: v.y/l, z: v.z/l };
  };
  const t1 = P('mixamorig1RightHandThumb1_036');
  const t4 = P('mixamorig1RightHandThumb4_039');
  const kP = P('mixamorig1RightHandPinky1_052');
  const p4 = P('mixamorig1RightHandPinky4_055');
  const kI = P('mixamorig1RightHandIndex1_040');
  const i4 = P('mixamorig1RightHandIndex4_043');
  const w = P('mixamorig1RightHand_035');
  if (!t1 || !t4 || !kP || !p4 || !w || !kI) return { error: 'huesos' };
  const th = nrm(sub(t4, t1));
  const pk = nrm(sub(p4, kP));
  const palm = Math.hypot(w.x-kI.x, w.y-kI.y, w.z-kI.z) || 1;
  const ang = Math.acos(Math.max(-1, Math.min(1, dot(th, pk)))) * 180 / Math.PI;
  return {
    thSide: th.x, thUp: th.y, thFwd: th.z,
    pkSide: pk.x, pkUp: pk.y, pkFwd: pk.z,
    horns: ang,
    fist: Math.hypot(i4.x-kI.x, i4.y-kI.y, i4.z-kI.z) / palm,
  };
}
"""
)


def abrir(p):
    browser = p.chromium.launch(
        args=[
            "--use-gl=swiftshader",
            "--enable-webgl",
            "--ignore-gpu-blocklist",
            "--enable-unsafe-swiftshader",
        ]
    )
    page = browser.new_page(viewport={"width": 1100, "height": 900})
    if VISOR_CACHE.exists():
        page.route(
            "**/@google/model-viewer*/**",
            lambda ruta: ruta.fulfill(
                path=str(VISOR_CACHE), content_type="application/javascript"
            ),
        )
    page.goto(se9.URL, wait_until="domcontentloaded", timeout=120000)
    page.wait_for_selector("#anim-info", timeout=30000, state="attached")
    listo = False
    for i in range(180):
        if page.evaluate(
            "() => !!(window.__LSM_CONTROLLER__ && window.__LSM_CONTROLLER__.isModelReady())"
        ):
            listo = True
            break
        if i % 10 == 0:
            estado = page.inner_text("#anim-info").strip()[:160]
            print(f"  espera {i*0.4:.0f}s: {estado}")
        time.sleep(0.4)
    if not listo:
        estado = page.inner_text("#anim-info").strip()[:200]
        browser.close()
        raise RuntimeError("El modelo 3D no cargo. Estado: " + estado)
    time.sleep(1.2)
    return browser, page


def pose_y(wx=0, wy=0, wz=0, p_spread=18, tcurl=0.0, taside=0.8,
           fist=0.98, t1=None, fx=12, fz=-8, arm_z=-18):
    extra = {ARM: {"z": arm_z}, FOREARM: {"x": fx, "z": fz}}
    if t1:
        extra[T1] = t1
    pinky = {"curl": 0.0}
    if p_spread:
        pinky["spread"] = p_spread
    pose = {
        "thumb": {"curl": tcurl, "aside": taside},
        "index": {"curl": fist},
        "middle": {"curl": fist},
        "ring": {"curl": fist},
        "pinky": pinky,
        "extra": extra,
    }
    muneca = {}
    if wx:
        muneca["x"] = wx
    if wy:
        muneca["y"] = wy
    if wz:
        muneca["z"] = wz
    if muneca:
        pose["muneca"] = muneca
    return pose


def linea(nombre, m):
    if m.get("error"):
        return f"{nombre:16s} {m}"
    return (
        f"{nombre:16s} th=({m['thSide']:+.2f},{m['thUp']:+.2f},{m['thFwd']:+.2f}) "
        f"pk=({m['pkSide']:+.2f},{m['pkUp']:+.2f},{m['pkFwd']:+.2f}) "
        f"horns={m['horns']:.0f} fist={m['fist']:.2f}"
    )


def asegurar_ref():
    REF.parent.mkdir(parents=True, exist_ok=True)
    if REF_SRC.exists():
        shutil.copy2(REF_SRC, REF)
    return REF if REF.exists() else None


def main():
    catalogo = json.loads(CATALOGO.read_text(encoding="utf-8"))
    actual = next(s for s in catalogo["senas"] if s["letra"] == "Y")["pose"]
    ref = asegurar_ref()

    casos = {
        "00_catalogo": actual,
        "01_base": pose_y(),
        "02_z-35": pose_y(wz=-35),
        "03_z-50": pose_y(wz=-50),
        "04_z-65": pose_y(wz=-65),
        "05_z35": pose_y(wz=35),
        "06_z50": pose_y(wz=50),
        "07_z-50_wx12": pose_y(wz=-50, wx=12),
        "08_z-50_ps28": pose_y(wz=-50, p_spread=28),
        "09_z-50_t1": pose_y(wz=-50, t1={"y": 16, "z": 12}),
        "10_I": next(s for s in catalogo["senas"] if s["letra"] == "I")["pose"],
    }

    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 1100, "height": 900})
        time.sleep(1.5)
        free_camera(page)
        viewer = page.query_selector("#viewer")

        items = [("REF foto", ref)] if ref else []
        prods = [("REF foto", ref)] if ref else []
        medidas = {}
        for nombre, pose in casos.items():
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
            time.sleep(0.35)
            m = page.evaluate(MEASURE_JS)
            medidas[nombre] = m
            print(" ", linea(nombre, m))

            cam(page, CAM_TARGET, CAM_ORBIT, CAM_FOV)
            ruta = OUT / f"{nombre}.png"
            captura(page, ruta, huesos=MANO, margen=0.55, lado=420)
            items.append((nombre, ruta))
            prod = OUT / f"{nombre}_prod.png"
            viewer.screenshot(path=str(prod))
            prods.append((nombre, prod))

        hoja(items, OUT / "_mano.png", cols=4, cell=320, titulo="Y · orientación")
        hoja(prods, OUT / "_prod.png", cols=4, cell=280, titulo="Y · producción")
        (OUT / "_medidas.json").write_text(
            json.dumps(medidas, indent=2), encoding="utf-8"
        )
        browser.close()
    print("listo", OUT)


if __name__ == "__main__":
    main()
