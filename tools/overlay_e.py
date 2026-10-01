"""Proyecta los huesos de la mano sobre la captura del avatar.

Sin esto no hay forma fiable de juzgar la pose: el sombreado del modelo hace
que una mano cerrada parezca abierta segun el angulo. Con los huesos dibujados
encima se ve exactamente donde cae cada yema.
"""
from PIL import Image, ImageDraw

from skel_e import CADENAS

# Proyecta con la camara activa de model-viewer y devuelve pixeles del canvas.
PROJECT_JS = """
(nombres) => {
  const mv = document.getElementById('handViewer');
  let scene = null;
  for (const sym of Object.getOwnPropertySymbols(mv)) {
    const v = mv[sym];
    if (v && typeof v.traverse === 'function') { scene = v; break; }
    if (v && v.model && typeof v.model.traverse === 'function') { scene = v.model; break; }
    if (v && v.target && typeof v.target.traverse === 'function') { scene = v.target; break; }
  }
  if (!scene) return { error: 'no-scene' };
  const cam = scene.camera || (scene.getCamera && scene.getCamera());
  if (!cam) return { error: 'no-camera', keys: Object.keys(scene) };
  scene.updateMatrixWorld(true);
  cam.updateMatrixWorld(true);
  if (cam.updateProjectionMatrix) cam.updateProjectionMatrix();

  const B = {};
  scene.traverse((o) => { if (o && o.name) B[o.name] = o; });
  // el canvas del shadow DOM devuelve 0x0 en headless; el elemento si mide bien
  const canvas = mv.shadowRoot ? mv.shadowRoot.querySelector('canvas') : null;
  let rect = canvas ? canvas.getBoundingClientRect() : null;
  if (!rect || !rect.width || !rect.height) rect = mv.getBoundingClientRect();

  // proyeccion manual: v_clip = P * V * p_world
  const pv = [];
  const m = cam.projectionMatrix.elements;
  const v = cam.matrixWorldInverse.elements;
  function mul(a, b) {
    const r = new Array(16);
    for (let i = 0; i < 4; i++) for (let j = 0; j < 4; j++) {
      let s = 0;
      for (let k = 0; k < 4; k++) s += a[k * 4 + j] * b[i * 4 + k];
      r[i * 4 + j] = s;
    }
    return r;
  }
  const mvp = mul(m, v);
  const out = {};
  nombres.forEach((n) => {
    const b = B[n];
    if (!b) return;
    const e = b.matrixWorld.elements;
    const x = e[12], y = e[13], z = e[14];
    const cx = mvp[0]*x + mvp[4]*y + mvp[8]*z + mvp[12];
    const cy = mvp[1]*x + mvp[5]*y + mvp[9]*z + mvp[13];
    const cw = mvp[3]*x + mvp[7]*y + mvp[11]*z + mvp[15];
    if (!cw) return;
    const ndcX = cx / cw, ndcY = cy / cw;
    // coordenadas de viewport: coinciden con los pixeles de page.screenshot()
    out[n] = [
      (ndcX * 0.5 + 0.5) * rect.width + rect.left,
      (-ndcY * 0.5 + 0.5) * rect.height + rect.top,
    ];
  });
  return { pts: out, rect: { w: rect.width, h: rect.height } };
}
"""

COLORES = {
    "pulgar": (220, 40, 40),
    "indice": (40, 120, 230),
    "medio": (40, 180, 70),
    "anular": (255, 140, 20),
    "menique": (170, 100, 220),
}


def nombres_huesos():
    vistos = []
    for cad in CADENAS.values():
        for n in cad:
            if n not in vistos:
                vistos.append(n)
    return vistos


def dibujar_overlay(img_path, pts, out_path):
    img = Image.open(img_path).convert("RGB")
    d = ImageDraw.Draw(img)
    for dedo, cadena in CADENAS.items():
        col = COLORES[dedo]
        seq = [tuple(pts[n]) for n in cadena if n in pts]
        if len(seq) > 1:
            d.line(seq, fill=col, width=3)
        for i, p in enumerate(seq):
            r = 5 if i == len(seq) - 1 else 3
            d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=col)
        if seq:
            d.text((seq[-1][0] + 6, seq[-1][1] - 6), dedo[:3], fill=col)
    img.save(out_path)
    return out_path
