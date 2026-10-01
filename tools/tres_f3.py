"""F: juntar los tres dedos hasta que se toquen pero se sigan distinguiendo.

Dos partes:

1. Un solucionador. `nudillos` traslada las raices de los cuatro dedos hacia la
   del medio (sin girarlas) y el eje z de cada raiz mueve la punta de lado, asi
   que para un hueco objetivo `w` entre ejes de dedos vecinos se ajustan por
   Newton los grados de anular y menique hasta medirlo.

2. El juez de verdad, que es la imagen. La distancia entre ejes no dice si la
   piel se toca: hay que mirar el perfil de brillo de una franja horizontal en la
   vista frontal. Si entre dos dedos aparece el fondo, estan separados; si el
   valle de sombra desaparece, se han fundido en un bloque y ya no se leen tres
   dedos.
"""
import time
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

from lab_e2 import MARCO_JS, abrir, hoja, orbita, preparar
from pinza_f3 import encuadrar
from tres_f import BASE, TRES_JS

OUT = Path(__file__).resolve().parents[1] / "tools" / "screenshots" / "tres_f3"

# Sensibilidad medida en tres_f2: grados de z en la raiz -> palmas de hueco.
D_MR_ZR = 0.0112    # z del anular sobre el hueco medio-anular
D_RP_ZR = -0.0083   # z del anular sobre el hueco anular-menique
D_RP_ZP = 0.0069    # z del menique sobre el hueco anular-menique

PIXELES_JS = """
() => {
  const mv = document.getElementById('handViewer');
  let s = null;
  for (const sym of Object.getOwnPropertySymbols(mv)) {
    const v = mv[sym];
    if (v && typeof v.traverse === 'function') { s = v; break; }
    if (v && v.model && typeof v.model.traverse === 'function') { s = v.model; break; }
    if (v && v.target && typeof v.target.traverse === 'function') { s = v.target; break; }
  }
  s.updateMatrixWorld(true);
  const cam = s.camera || (s.getCamera && s.getCamera());
  if (cam) cam.updateMatrixWorld(true);
  const B = {};
  s.traverse((o) => { if (o && o.name) B[o.name] = o; });
  const P = (n) => { const e = B[n].matrixWorld.elements; return { x: e[12], y: e[13], z: e[14] }; };
  const pm = cam.projectionMatrix.elements, vm = cam.matrixWorldInverse.elements;
  const mvp = new Array(16);
  for (let i = 0; i < 4; i++) for (let j = 0; j < 4; j++) {
    let acc = 0;
    for (let k = 0; k < 4; k++) acc += pm[k*4+j] * vm[i*4+k];
    mvp[i*4+j] = acc;
  }
  const r = mv.getBoundingClientRect();
  const px = (p) => {
    const w = mvp[3]*p.x + mvp[7]*p.y + mvp[11]*p.z + mvp[15] || 1;
    const nx = (mvp[0]*p.x + mvp[4]*p.y + mvp[8]*p.z + mvp[12]) / w;
    const ny = (mvp[1]*p.x + mvp[5]*p.y + mvp[9]*p.z + mvp[13]) / w;
    return { x: (nx * 0.5 + 0.5) * r.width, y: (-ny * 0.5 + 0.5) * r.height };
  };
  const out = { ancho: r.width, alto: r.height };
  ['Middle', 'Ring', 'Pinky', 'Index'].forEach((d) => {
    out[d] = [1,2,3,4].map((k) => px(P('RightHand' + d + k)));
  });
  return out;
}
"""

CENTRO_JS = """
() => {
  const mv = document.getElementById('handViewer');
  let s = null;
  for (const sym of Object.getOwnPropertySymbols(mv)) {
    const v = mv[sym];
    if (v && typeof v.traverse === 'function') { s = v; break; }
    if (v && v.model && typeof v.model.traverse === 'function') { s = v.model; break; }
    if (v && v.target && typeof v.target.traverse === 'function') { s = v.target; break; }
  }
  s.updateMatrixWorld(true);
  const B = {};
  s.traverse((o) => { if (o && o.name) B[o.name] = o; });
  const P = (n) => { const e = B[n].matrixWorld.elements; return { x: e[12], y: e[13], z: e[14] }; };
  const pts = ['Middle', 'Ring', 'Pinky'].map((d) => P('RightHand' + d + '3'));
  const off = (s.target && s.target.position) || { x: 0, y: 0, z: 0 };
  return {
    x: pts.reduce((a, p) => a + p.x, 0) / 3 - off.x,
    y: pts.reduce((a, p) => a + p.y, 0) / 3 - off.y,
    z: pts.reduce((a, p) => a + p.z, 0) / 3 - off.z,
  };
}
"""


def pose(nudillos, zM, zR, zP, largo=None, index=None, thumb=None):
    p = {k: (dict(v) if isinstance(v, dict) else v) for k, v in BASE.items()}
    p["extra"] = {"RightHandThumb1": {"z": 50}}
    for dedo, z in (("Middle", zM), ("Ring", zR), ("Pinky", zP)):
        if z:
            p["extra"][f"RightHand{dedo}1"] = {"z": z}
    if nudillos:
        p["nudillos"] = nudillos
    if largo:
        p["largo"] = largo
    if index:
        p["index"] = dict(index)
    if thumb:
        p["thumb"] = dict(thumb)
    return p


def resolver(page, nudillos, objetivo, largo=None, vueltas=4):
    """Grados de z en anular y menique para que los dos huecos midan `objetivo`."""
    zR, zP = 0.0, 0.0
    m = None
    for _ in range(vueltas):
        page.evaluate(
            "(x) => window.__LSM_CONTROLLER__.applyTestPose(x)",
            pose(nudillos, 0, zR, zP, largo),
        )
        m = page.evaluate(TRES_JS)
        mr, rp = m["mr"]["distal"], m["rp"]["distal"]
        if abs(mr - objetivo) < 0.004 and abs(rp - objetivo) < 0.004:
            break
        zR += (objetivo - mr) / D_MR_ZR
        rp_prev = rp + (objetivo - mr) / D_MR_ZR * D_RP_ZR  # lo que movera el anular
        zP += (objetivo - rp_prev) / D_RP_ZP
        zR = max(-40, min(40, zR))
        zP = max(-40, min(40, zP))
    return zR, zP, m


def franja(img, pix, fondo_lum=None):
    """Perfil de brillo entre los tres dedos: fondo visible y valle de la costura."""
    gris = img.convert("L")
    w, h = gris.size
    esc = w / pix["ancho"]
    dedos = {}
    for d in ("Middle", "Ring", "Pinky"):
        dedos[d] = [(p["x"] * esc, p["y"] * esc) for p in pix[d]]
    # franja entre la punta del menique (el dedo mas corto) y los nudillos
    y0 = max(dedos["Pinky"][3][1], min(d[2][1] for d in dedos.values()))
    y1 = min(d[1][1] for d in dedos.values())
    if y1 <= y0:
        y0, y1 = y1, y0
    filas = [int(y) for y in range(int(y0) + 4, int(y1) - 4) if 0 <= y < h]
    if len(filas) < 8:
        return None
    if fondo_lum is None:
        fondo_lum = min(gris.getpixel((2, 2)), gris.getpixel((w - 3, 2)))

    def centro_x(d, y):
        pts = dedos[d]
        for a, b in zip(pts, pts[1:]):
            if (a[1] - y) * (b[1] - y) <= 0 and a[1] != b[1]:
                t = (y - a[1]) / (b[1] - a[1])
                return a[0] + (b[0] - a[0]) * t
        return min(pts, key=lambda p: abs(p[1] - y))[0]

    res = {"fondo": 0.0, "costura": [], "filas": len(filas)}
    huecos = 0
    costuras = {"MR": [], "RP": []}
    for y in filas:
        fila = [gris.getpixel((x, y)) for x in range(w)]
        cx = {d: centro_x(d, y) for d in dedos}
        for etiqueta, (a, b) in (("MR", ("Middle", "Ring")), ("RP", ("Ring", "Pinky"))):
            xa, xb = sorted((cx[a], cx[b]))
            xa, xb = int(max(0, xa)), int(min(w - 1, xb))
            if xb - xa < 4:
                continue
            tramo = fila[xa:xb]
            pico = max(max(fila[max(0, xa - 3):xa + 4]), max(fila[xb - 3:min(w, xb + 4)]))
            valle = min(tramo)
            if valle <= fondo_lum + 12:
                huecos += 1          # entre los dedos se ve el fondo
            elif pico > 0:
                costuras[etiqueta].append((pico - valle) / pico)
    res["fondo"] = huecos / max(1, len(filas) * 2)
    for etiqueta in ("MR", "RP"):
        v = costuras[etiqueta]
        res[etiqueta] = sum(v) / len(v) if v else 0.0
    return res


CANDIDATOS = [
    ("00 como esta", 0.0, None, None),
    ("01 w0.21", 0.0, 0.21, None),
    ("02 w0.19", 0.15, 0.19, None),
    ("03 w0.17", 0.25, 0.17, None),
    ("04 w0.16", 0.3, 0.16, None),
    ("05 w0.15", 0.35, 0.15, None),
    ("06 w0.14", 0.35, 0.14, None),
    ("07 w0.13", 0.4, 0.13, None),
    ("08 w0.15 largo", 0.35, 0.15, {"pinky": 1.05, "ring": 1.02}),
]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    fichas = []
    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 900, "height": 950})
        time.sleep(0.5)
        preparar(page)
        for nombre, nud, w, largo in CANDIDATOS:
            if w is None:
                zR = zP = 0.0
                page.evaluate(
                    "(x) => window.__LSM_CONTROLLER__.applyTestPose(x)",
                    pose(nud, 0, 0, 0, largo),
                )
                m = page.evaluate(TRES_JS)
            else:
                zR, zP, m = resolver(page, nud, w, largo)
            marco = page.evaluate(MARCO_JS)
            c = page.evaluate(CENTRO_JS)
            encuadrar(
                page,
                orbita(marco, (1.0, 0.0, 0.0), radio_palmas=2.6),
                "20deg",
                "%.4fm %.4fm %.4fm" % (c["x"], c["y"], c["z"]),
            )
            destino = OUT / f"{nombre.split()[0]}_frente.png"
            page.query_selector("#handViewer").screenshot(path=str(destino))
            pix = page.evaluate(PIXELES_JS)
            an = franja(Image.open(destino), pix)
            fichas.append((nombre, nud, zR, zP, m, an, destino))
            print(
                f"{nombre:16s} nud={nud:.2f} zR={zR:+6.1f} zP={zP:+6.1f} "
                f"huecos mr={m['mr']['distal']:.3f} rp={m['rp']['distal']:.3f} "
                f"pinza={m['pinza']:.3f} | imagen fondo={an['fondo']:.2f} "
                f"costura MR={an['MR']:.3f} RP={an['RP']:.3f}"
            )
        browser.close()

    print("hoja:", hoja([(f[0], f[6]) for f in fichas], OUT / "_frente.png", cols=3, cell=340))


if __name__ == "__main__":
    main()
