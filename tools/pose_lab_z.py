"""Z lab 1: forma de la lamina + que huesos dibujan la Z con la punta.

La Z del catalogo es solo un indice arriba, quieto. En la foto el indice
senala hacia arriba, el resto va en puno y palma al frente; las lineas vino
son el trazo de una Z mayuscula: derecha, diagonal abajo-izquierda, derecha.

La punta del indice es el lapiz. El dedo no cambia de forma: se mueve la
mano entera (muneca + antebrazo + hombro) para que la yema recorra esas
tres rayas.
"""
import json
import shutil
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from enfoque_r import MANO, captura, hoja
from pose_lab_e import ARM, T1, _GET_SCENE, free_camera
from pose_lab_x2 import FOREARM
from search_e9 import VISOR_CACHE
from ver_s import CAM_FOV, CAM_ORBIT, CAM_TARGET
import search_e9 as se9

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "lab_z"
OUT.mkdir(parents=True, exist_ok=True)
CATALOGO = ROOT / "data" / "catalogo-lsm.json"
REF_SRC = Path(
    r"C:\Users\KZTRDG\.cursor\projects"
    r"\c-Users-KZTRDG-General-Motors-Christian-Osvaldo-Partida-Cadena-Becarios-Manu-Lenguaje-de-se-as"
    r"\assets"
    r"\c__Users_KZTRDG_AppData_Roaming_Cursor_User_workspaceStorage"
    r"_e58e5485bac69e9b6ccd69cb178bd5da_images_image-cc628323-fd51-4a16-b394-62b7c170bf85.png"
)
REF = ROOT / "tools" / "screenshots" / "referencia" / "Z_usuario.png"

se9.URL = "http://127.0.0.1:8006/practica.html?letra=%E2%97%8B&v=z1"

WRIST = "mixamorig1RightHand_035"


def abrir(p):
    browser = p.chromium.launch(
        channel="chrome",
        args=[
            "--use-gl=swiftshader",
            "--enable-webgl",
            "--ignore-gpu-blocklist",
            "--enable-unsafe-swiftshader",
        ],
    )
    page = browser.new_page(viewport={"width": 1100, "height": 900})
    modelo = ROOT / "model2.glb"
    if modelo.exists():
        page.route(
            "**/model2.glb*",
            lambda ruta: ruta.fulfill(
                path=str(modelo), content_type="model/gltf-binary"
            ),
        )
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
  const nrm = (v) => {
    const l = Math.hypot(v.x, v.y, v.z) || 1;
    return { x: v.x/l, y: v.y/l, z: v.z/l };
  };
  const d = (a, b) => Math.hypot(a.x-b.x, a.y-b.y, a.z-b.z);

  const w = P('mixamorig1RightHand_035');
  const i1 = P('mixamorig1RightHandIndex1_040');
  const i4 = P('mixamorig1RightHandIndex4_043');
  const m1 = P('mixamorig1RightHandMiddle1_044');
  const m4 = P('mixamorig1RightHandMiddle4_047');
  const t1 = P('mixamorig1RightHandThumb1_036');
  const t4 = P('mixamorig1RightHandThumb4_039');
  if (!w || !i1 || !i4 || !m1 || !m4) return { error: 'huesos' };
  const palm = d(w, i1) || 1;
  const idx = nrm(sub(i4, i1));
  return {
    palm,
    idxUp: idx.y, idxSide: idx.x, idxFwd: idx.z,
    idxLen: d(i4, i1) / palm,
    midLen: d(m4, m1) / palm,
    thumbLen: t1 && t4 ? d(t4, t1) / palm : null,
    tipX: i4.x, tipY: i4.y, tipZ: i4.z,
  };
}
"""
)

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
  const palm = Math.hypot(w.x-i1.x, w.y-i1.y, w.z-i1.z) || 1;
  return { palm, x: i4.x, y: i4.y, z: i4.z };
}
"""
)

EJES = [
    (ARM, "x", 8),
    (ARM, "y", 8),
    (ARM, "z", 8),
    (FOREARM, "x", 8),
    (FOREARM, "y", 8),
    (FOREARM, "z", 8),
]


def pose_z(
    wx=0,
    wy=0,
    wz=0,
    tcurl=0.55,
    taside=0.12,
    fist=0.98,
    idx=0.0,
    arm_z=-18,
    ax=0,
    ay=0,
    fx=0,
    fz=0,
    t1=None,
):
    extra = {ARM: {"z": arm_z}}
    if ax:
        extra[ARM]["x"] = ax
    if ay:
        extra[ARM]["y"] = ay
    if fx or fz:
        extra[FOREARM] = {}
        if fx:
            extra[FOREARM]["x"] = fx
        if fz:
            extra[FOREARM]["z"] = fz
    if t1:
        extra[T1] = t1
    pose = {
        "thumb": {"curl": tcurl, "aside": taside},
        "index": {"curl": idx},
        "middle": {"curl": fist},
        "ring": {"curl": fist},
        "pinky": {"curl": fist},
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


def cam(page):
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
    time.sleep(0.2)


def aplicar(page, pose):
    page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
    time.sleep(0.25)


def con_extra(base, hueso, eje, grados):
    pose = json.loads(json.dumps(base))
    extra = pose.setdefault("extra", {})
    extra.setdefault(hueso, {})
    extra[hueso][eje] = extra[hueso].get(eje, 0) + grados
    return pose


def linea(nombre, m):
    if m.get("error"):
        return f"{nombre:18s} {m}"
    return (
        f"{nombre:18s} idx=({m['idxSide']:+.2f},{m['idxUp']:+.2f},{m['idxFwd']:+.2f}) "
        f"len={m['idxLen']:.2f} mid={m['midLen']:.2f} th={m['thumbLen']:.2f}"
    )


def asegurar_ref():
    REF.parent.mkdir(parents=True, exist_ok=True)
    if REF_SRC.exists():
        shutil.copy2(REF_SRC, REF)
    return REF if REF.exists() else None


def main():
    catalogo = json.loads(CATALOGO.read_text(encoding="utf-8"))
    actual = next(s for s in catalogo["senas"] if s["letra"] == "Z")["pose"]
    ref = asegurar_ref()

    casos = {
        "00_catalogo": actual,
        "01_base": pose_z(),
        "10_wx-40": pose_z(wx=-40),
        "11_wx-70": pose_z(wx=-70),
        "12_wx-90": pose_z(wx=-90),
        "13_wx-70_wy20": pose_z(wx=-70, wy=20),
        "14_wx-70_wz-25": pose_z(wx=-70, wz=-25),
        "15_wx-50_wy-15": pose_z(wx=-50, wy=-15),
    }

    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 1100, "height": 900})
        time.sleep(0.4)
        free_camera(page)
        viewer = page.query_selector("#viewer")

        items = [("REF foto", ref)] if ref else []
        prods = [("REF foto", ref)] if ref else []
        medidas = {}
        for nombre, pose in casos.items():
            aplicar(page, pose)
            m = page.evaluate(MEASURE_JS)
            medidas[nombre] = m
            print(" ", linea(nombre, m))
            cam(page)
            ruta = OUT / f"{nombre}.png"
            captura(page, ruta, huesos=MANO, margen=0.55, lado=420)
            items.append((nombre, ruta))
            prod = OUT / f"{nombre}_prod.png"
            viewer.screenshot(path=str(prod))
            prods.append((nombre, prod))
            time.sleep(0.15)

        try:
            hoja(items, OUT / "_mano.png", cols=4, cell=320, titulo="Z · forma")
            hoja(prods, OUT / "_prod.png", cols=4, cell=280, titulo="Z · produccion")
        except OSError as err:
            print("hoja omitida:", err)

        base = pose_z()
        aplicar(page, base)
        origen = page.evaluate(POS_JS)
        palm = origen["palm"]
        print(f"\njacobiano palma={palm:.4f}")
        print(f"{'hueso':34s} {'eje':4s} {'dx':>9s} {'dy':>9s} {'dz':>9s}")
        jac = {}
        for hueso, eje, paso in EJES:
            aplicar(page, con_extra(base, hueso, eje, paso))
            m = page.evaluate(POS_JS)
            dx = (m["x"] - origen["x"]) / paso / palm
            dy = (m["y"] - origen["y"]) / paso / palm
            dz = (m["z"] - origen["z"]) / paso / palm
            jac[f"{hueso}.{eje}"] = {"dx": dx, "dy": dy, "dz": dz}
            corto = hueso.replace("mixamorig1Right", "")
            print(f"{corto:34s} {eje:4s} {dx:+9.4f} {dy:+9.4f} {dz:+9.4f}")

        (OUT / "_medidas.json").write_text(
            json.dumps({"forma": medidas, "palm": palm, "jac": jac}, indent=2),
            encoding="utf-8",
        )
        browser.close()
    print("listo", OUT)


if __name__ == "__main__":
    main()
