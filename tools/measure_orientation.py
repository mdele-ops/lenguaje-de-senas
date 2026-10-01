"""Mide como queda orientada la mano en el espacio del visor.

Devuelve, para la pose indicada (por defecto Neutral), tres vectores unitarios:
  dedos  = muneca -> nudillo medio (hacia donde apuntan los dedos)
  palma  = normal de la palma (sale por la cara palmar)
  pulgar = muneca -> base del pulgar

Con camera-orbit theta=0 la camara esta sobre +Z mirando hacia -Z, asi que la
lectura correcta del alfabeto pide dedos ~ +Y y palma ~ +Z.
"""
import json
import sys
import time

from playwright.sync_api import sync_playwright

from render_letters import CHROME_ARGS, load_senas, open_ready_page

BONES_JS = """
() => {
  const mv = document.getElementById('handViewer');
  function getScene(m) {
    if (m.model && typeof m.model.traverse === 'function') return m.model;
    if (m.model && m.model.scene && typeof m.model.scene.traverse === 'function') return m.model.scene;
    for (const s of Object.getOwnPropertySymbols(m)) {
      const v = m[s];
      if (v && typeof v.traverse === 'function') return v;
      if (v && v.model && typeof v.model.traverse === 'function') return v.model;
      if (v && v.target && typeof v.target.traverse === 'function') return v.target;
    }
    return null;
  }
  const scene = getScene(mv);
  scene.updateMatrixWorld(true);
  const bones = {};
  scene.traverse((o) => { if (o && o.name) bones[o.name] = o; });
  const want = [
    'mixamorig1RightArm_033', 'mixamorig1RightForeArm_034', 'mixamorig1RightHand_035',
    'mixamorig1RightHandThumb1_036', 'mixamorig1RightHandThumb4_039',
    'mixamorig1RightHandIndex1_040', 'mixamorig1RightHandIndex4_043',
    'mixamorig1RightHandMiddle1_044', 'mixamorig1RightHandMiddle4_047',
    'mixamorig1RightHandPinky1_052', 'mixamorig1RightHandPinky4_055',
  ];
  const out = {};
  for (const n of want) {
    const b = bones[n];
    if (!b) continue;
    const e = b.matrixWorld.elements;
    out[n.replace('mixamorig1Right', '').replace(/_\\d+$/, '')] = [e[12], e[13], e[14]];
  }
  return out;
}
"""


def sub(a, b):
    return [a[i] - b[i] for i in range(3)]


def norm(v):
    m = sum(c * c for c in v) ** 0.5 or 1.0
    return [round(c / m, 3) for c in v]


def cross(a, b):
    return [
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    ]


def report(pts, label):
    wrist = pts["Hand"]
    mid_knuckle = pts["HandMiddle1"]
    index_knuckle = pts["HandIndex1"]
    pinky_knuckle = pts["HandPinky1"]

    dedos = norm(sub(mid_knuckle, wrist))
    # De indice a menique cruzado con la direccion de los dedos da la normal.
    across = sub(pinky_knuckle, index_knuckle)
    palma = norm(cross(across, sub(mid_knuckle, wrist)))
    antebrazo = norm(sub(wrist, pts["ForeArm"]))

    print(f"--- {label} ---")
    print("  antebrazo (codo->muneca):", antebrazo)
    print("  dedos     (muneca->nudillo medio):", dedos)
    print("  palma     (normal palmar):", palma)
    print("  muneca (mundo):", [round(c, 3) for c in wrist])


def main():
    letra = (sys.argv[1] if len(sys.argv) > 1 else "○").upper()
    senas = load_senas()
    match = [s for s in senas if s["letra"].upper() == letra]
    pose = match[0].get("pose") if match else None

    with sync_playwright() as p:
        browser = p.chromium.launch(args=CHROME_ARGS)
        page = open_ready_page(browser)
        page.evaluate("(p) => window.__LSM_CONTROLLER__.applyTestPose(p)", pose)
        time.sleep(0.6)
        report(page.evaluate(BONES_JS), letra)
        browser.close()


if __name__ == "__main__":
    main()
