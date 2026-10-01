"""F: poner medio, anular y menique paralelos y acercarlos hasta que se toquen.

En la pose de reposo del rig los tres dedos divergen: la punta del medio cae
0.146 palmas hacia el pulgar respecto a su nudillo y la del menique 0.127 hacia
fuera. Primero se corrige eso con el eje z de cada raiz (quedan verticales y
paralelos, sin doblarlos), y despues `nudillos` acerca las raices hasta que la
piel se toca. El juez es el perfil de brillo de la imagen: si entre dos dedos se
ve el fondo estan separados, y si el valle de sombra desaparece se han fundido.
"""
import time
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

from lab_e2 import MARCO_JS, abrir, hoja, orbita, preparar
from pinza_f3 import encuadrar
from tres_f import BASE, TRES_JS
from tres_f3 import CENTRO_JS, PIXELES_JS, pose

OUT = Path(__file__).resolve().parents[1] / "tools" / "screenshots" / "tres_f4"

# tres_f2: palmas que mueve la punta cada grado de z en la raiz
SENS = {"Middle": 0.0159, "Ring": 0.0148, "Pinky": 0.0103}

DESVIO_JS = """
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
  const sub = (a, b) => ({ x: a.x-b.x, y: a.y-b.y, z: a.z-b.z });
  const dot = (a, b) => a.x*b.x + a.y*b.y + a.z*b.z;
  const len = (a) => Math.hypot(a.x, a.y, a.z);
  const nor = (a) => { const l = len(a) || 1; return { x: a.x/l, y: a.y/l, z: a.z/l }; };
  const wrist = P('RightHand'), kI = P('RightHandIndex1'), kM = P('RightHandMiddle1');
  const kP = P('RightHandPinky1');
  const palm = len(sub(kM, wrist)) || 1;
  const ancho = nor(sub(kP, kI));
  const lado = (p) => dot(sub(p, kI), ancho) / palm;
  const out = {};
  ['Middle', 'Ring', 'Pinky'].forEach((d) => {
    // cuanto se desvia la punta del dedo respecto a su propio nudillo
    out[d] = lado(P('RightHand' + d + '4')) - lado(P('RightHand' + d + '1'));
  });
  return out;
}
"""


def paralelos(page, nudillos, largo=None, vueltas=5):
    """Grados de z que dejan cada punta encima de su nudillo (dedos paralelos)."""
    z = {"Middle": 0.0, "Ring": 0.0, "Pinky": 0.0}
    for _ in range(vueltas):
        page.evaluate(
            "(x) => window.__LSM_CONTROLLER__.applyTestPose(x)",
            pose(nudillos, z["Middle"], z["Ring"], z["Pinky"], largo),
        )
        d = page.evaluate(DESVIO_JS)
        if max(abs(v) for v in d.values()) < 0.006:
            break
        for dedo in z:
            z[dedo] -= d[dedo] / SENS[dedo]
    return z


def franja(img, pix):
    """Fondo visible entre dedos y contraste del valle, en la franja del menique."""
    gris = img.convert("L")
    w, h = gris.size
    esc = w / pix["ancho"]
    dedos = {d: [(p["x"] * esc, p["y"] * esc) for p in pix[d]] for d in ("Middle", "Ring", "Pinky")}
    # el menique es el dedo corto: su falange media es la franja donde estan los tres
    y0, y1 = sorted((dedos["Pinky"][2][1], dedos["Pinky"][1][1]))
    filas = [y for y in range(int(y0) + 3, int(y1) - 3) if 0 <= y < h]
    if len(filas) < 6:
        return None
    fondo = min(gris.getpixel((2, 2)), gris.getpixel((w - 3, 2)), gris.getpixel((2, h - 3)))

    def centro_x(pts, y):
        for a, b in zip(pts, pts[1:]):
            if (a[1] - y) * (b[1] - y) <= 0 and a[1] != b[1]:
                return a[0] + (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1])
        return min(pts, key=lambda q: abs(q[1] - y))[0]

    separados = {"MR": 0, "RP": 0}
    contraste = {"MR": [], "RP": []}
    for y in filas:
        fila = [gris.getpixel((x, y)) for x in range(w)]
        cx = {d: centro_x(dedos[d], y) for d in dedos}
        for etq, (a, b) in (("MR", ("Middle", "Ring")), ("RP", ("Ring", "Pinky"))):
            xa, xb = sorted((cx[a], cx[b]))
            xa, xb = int(max(0, xa)), int(min(w - 1, xb))
            if xb - xa < 5:
                continue
            valle = min(fila[xa + 1:xb])
            pico = max(max(fila[max(0, xa - 4):xa + 5]), max(fila[xb - 4:min(w, xb + 5)]))
            if valle <= fondo + 14:
                separados[etq] += 1
            elif pico:
                contraste[etq].append((pico - valle) / pico)
    n = max(1, len(filas))
    return {
        "filas": n,
        "sepMR": separados["MR"] / n,
        "sepRP": separados["RP"] / n,
        "conMR": sum(contraste["MR"]) / len(contraste["MR"]) if contraste["MR"] else 0.0,
        "conRP": sum(contraste["RP"]) / len(contraste["RP"]) if contraste["RP"] else 0.0,
        "recorte": (
            int(min(min(p[0] for p in v) for v in dedos.values()) - 30),
            int(min(min(p[1] for p in v) for v in dedos.values()) - 20),
            int(max(max(p[0] for p in v) for v in dedos.values()) + 30),
            int(max(max(p[1] for p in v) for v in dedos.values()) + 20),
        ),
    }


CASOS = [
    ("00 como esta", None, None),
    ("01 paralelos nud0.00", 0.0, None),
    ("02 paralelos nud0.10", 0.10, None),
    ("03 paralelos nud0.20", 0.20, None),
    ("04 paralelos nud0.28", 0.28, None),
    ("05 paralelos nud0.36", 0.36, None),
    ("06 paralelos nud0.44", 0.44, None),
    ("07 nud0.28 largo", 0.28, {"pinky": 1.06, "ring": 1.02}),
    ("08 nud0.36 largo", 0.36, {"pinky": 1.06, "ring": 1.02}),
]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    fichas = []
    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 900, "height": 950})
        time.sleep(0.5)
        preparar(page)
        for nombre, nud, largo in CASOS:
            clave = nombre.split()[0]
            if nud is None:
                z = {"Middle": 0.0, "Ring": 0.0, "Pinky": 0.0}
                page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", BASE)
            else:
                z = paralelos(page, nud, largo)
            m = page.evaluate(TRES_JS)
            marco = page.evaluate(MARCO_JS)
            c = page.evaluate(CENTRO_JS)
            encuadrar(
                page,
                orbita(marco, (1.0, 0.0, 0.0), radio_palmas=2.4),
                "20deg",
                "%.4fm %.4fm %.4fm" % (c["x"], c["y"], c["z"]),
            )
            entera = OUT / f"{clave}_frente.png"
            page.query_selector("#handViewer").screenshot(path=str(entera))
            pix = page.evaluate(PIXELES_JS)
            an = franja(Image.open(entera), pix)
            zoom = OUT / f"{clave}_zoom.png"
            img = Image.open(entera)
            caja = an["recorte"] if an else (0, 0, img.width, img.height)
            img.crop(caja).save(zoom)
            fichas.append((nombre, zoom))
            print(
                f"{nombre:22s} z=M{z['Middle']:+.0f} R{z['Ring']:+.0f} P{z['Pinky']:+.0f} "
                f"ejes mr={m['mr']['distal']:.3f} rp={m['rp']['distal']:.3f} "
                f"pinza={m['pinza']:.3f} | "
                + (
                    f"fondo MR={an['sepMR']:.2f} RP={an['sepRP']:.2f} "
                    f"costura MR={an['conMR']:.3f} RP={an['conRP']:.3f}"
                    if an
                    else "imagen: franja demasiado corta"
                )
            )
        browser.close()

    print("hoja:", hoja(fichas, OUT / "_zoom.png", cols=3, cell=340))


if __name__ == "__main__":
    main()
