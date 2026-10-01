"""F: los tres dedos juntos, zona a zona, sin aplastar uno dentro de otro.

Que la franja de abajo no vea el fondo no basta: los dedos se juntan solos cerca
de los nudillos y se abren hacia las puntas. Aqui cada costura (medio-anular y
anular-menique) se mide en tres alturas -- junto a los nudillos, a media altura y
junto a las puntas -- y ademas se compara el ancho del bloque de los tres dedos
con tres anchos de dedo suelto: si el bloque sale mucho mas estrecho es que se
estan metiendo unos dentro de otros aunque la imagen parezca correcta.
"""
import time
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

from lab_e2 import MARCO_JS, abrir, hoja, orbita, preparar
from pinza_f3 import encuadrar
from tres_f import BASE, TRES_JS
from tres_f3 import CENTRO_JS, PIXELES_JS, pose
from tres_f4 import SENS, DESVIO_JS

OUT = Path(__file__).resolve().parents[1] / "tools" / "screenshots" / "tres_f5"

PIEL = 14  # margen de luminancia sobre el fondo para decidir "aqui se ve el fondo"


def paralelos(page, nudillos, cierre, largo=None, vueltas=5):
    """z de cada raiz para dejar los dedos paralelos, mas un cierre extra.

    `cierre` son los grados que el anular y el menique giran ademas de lo que
    hace falta para quedar verticales: acerca las puntas entre si (converger),
    que es lo que cierra el hueco sin mover las raices.
    """
    z = {"Middle": 0.0, "Ring": 0.0, "Pinky": 0.0}
    for _ in range(vueltas):
        page.evaluate(
            "(x) => window.__LSM_CONTROLLER__.applyTestPose(x)",
            pose(nudillos, z["Middle"], z["Ring"], z["Pinky"], largo),
        )
        d = page.evaluate(DESVIO_JS)
        if max(abs(v) for v in d.values()) < 0.005:
            break
        for dedo in z:
            z[dedo] -= d[dedo] / SENS[dedo]
    z["Ring"] -= cierre * 0.35
    z["Pinky"] -= cierre
    return z


def _runs(fila, fondo):
    """Tramos de piel (inicio, fin) de una fila de pixeles."""
    out = []
    ini = None
    for x, v in enumerate(fila):
        if v > fondo + PIEL:
            if ini is None:
                ini = x
        elif ini is not None:
            out.append((ini, x))
            ini = None
    if ini is not None:
        out.append((ini, len(fila)))
    return out


def analizar(img, pix):
    gris = img.convert("L")
    w, h = gris.size
    esc = w / pix["ancho"]
    dedos = {
        d: [(p["x"] * esc, p["y"] * esc) for p in pix[d]]
        for d in ("Middle", "Ring", "Pinky")
    }
    fondo = min(gris.getpixel((2, 2)), gris.getpixel((w - 3, 2)), gris.getpixel((2, h - 3)))
    filas = {y: [gris.getpixel((x, y)) for x in range(w)] for y in range(h)}

    def centro_x(pts, y):
        for a, b in zip(pts, pts[1:]):
            if (a[1] - y) * (b[1] - y) <= 0 and a[1] != b[1]:
                return a[0] + (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1])
        return None

    res = {}
    for etq, (a, b) in (("MR", ("Middle", "Ring")), ("RP", ("Ring", "Pinky"))):
        # de la punta del dedo mas corto del par hasta la fila de nudillos
        arriba = max(dedos[a][3][1], dedos[b][3][1])
        abajo = min(dedos[a][0][1], dedos[b][0][1])
        if abajo < arriba:
            arriba, abajo = abajo, arriba
        tramo = abajo - arriba
        zonas = {
            "punta": (arriba + tramo * 0.05, arriba + tramo * 0.35),
            "medio": (arriba + tramo * 0.35, arriba + tramo * 0.65),
            "base": (arriba + tramo * 0.65, arriba + tramo * 0.95),
        }
        for zona, (y0, y1) in zonas.items():
            visto = 0
            total = 0
            contraste = []
            for y in range(int(y0), int(y1)):
                if not (0 <= y < h):
                    continue
                ca, cb = centro_x(dedos[a], y), centro_x(dedos[b], y)
                if ca is None or cb is None:
                    continue
                xa, xb = sorted((int(ca), int(cb)))
                xa, xb = max(0, xa), min(w - 1, xb)
                if xb - xa < 5:
                    continue
                total += 1
                medio = filas[y][xa + 1:xb]
                valle = min(medio)
                pico = max(
                    max(filas[y][max(0, xa - 4):xa + 5]),
                    max(filas[y][xb - 4:min(w, xb + 5)]),
                )
                if valle <= fondo + PIEL:
                    visto += 1
                elif pico:
                    contraste.append((pico - valle) / pico)
            res[f"{etq}_{zona}"] = visto / total if total else None
            res[f"{etq}_{zona}_c"] = (
                sum(contraste) / len(contraste) if contraste else 0.0
            )

    # ancho de un dedo suelto: el medio por encima de la punta del anular
    y0 = dedos["Middle"][3][1] + 6
    y1 = dedos["Ring"][3][1] - 6
    anchos = []
    for y in range(int(y0), int(y1)):
        c = centro_x(dedos["Middle"], y)
        if c is None or not (0 <= y < h):
            continue
        for ini, fin in _runs(filas[y], fondo):
            if ini <= c <= fin:
                anchos.append(fin - ini)
    suelto = sorted(anchos)[len(anchos) // 2] if anchos else None

    # ancho del bloque de los tres, a media altura del menique
    yp = (dedos["Pinky"][3][1] + dedos["Pinky"][1][1]) / 2
    bloque = None
    for y in (int(yp), int(yp) - 3, int(yp) + 3):
        if not (0 <= y < h):
            continue
        cs = [centro_x(dedos[d], y) for d in dedos]
        if any(c is None for c in cs):
            continue
        for ini, fin in _runs(filas[y], fondo):
            if ini <= min(cs) and max(cs) <= fin:
                bloque = fin - ini
                break
        if bloque:
            break
    res["suelto"] = suelto
    res["bloque"] = bloque
    res["aplastado"] = (bloque / (3 * suelto)) if (bloque and suelto) else None
    res["recorte"] = (
        int(min(min(p[0] for p in v) for v in dedos.values()) - 40),
        int(min(min(p[1] for p in v) for v in dedos.values()) - 25),
        int(max(max(p[0] for p in v) for v in dedos.values()) + 40),
        int(max(max(p[1] for p in v) for v in dedos.values()) + 25),
    )
    return res


CASOS = [
    ("00 actual", None, 0, None),
    ("01 par nud0 c0", 0.0, 0, None),
    ("02 par nud0 c6", 0.0, 6, None),
    ("03 par nud0 c12", 0.0, 12, None),
    ("04 par nud0.12 c6", 0.12, 6, None),
    ("05 par nud0.12 c12", 0.12, 12, None),
    ("06 par nud0.2 c6", 0.20, 6, None),
    ("07 par nud0.2 c12", 0.20, 12, None),
    ("08 par nud0.28 c8", 0.28, 8, None),
    ("09 nud0.12 c12 largo", 0.12, 12, {"pinky": 1.06, "ring": 1.02}),
    ("10 nud0.2 c8 largo", 0.20, 8, {"pinky": 1.06, "ring": 1.02}),
]


def fila_informe(nombre, z, m, an):
    def pc(clave):
        v = an.get(clave)
        return "  - " if v is None else f"{v:4.2f}"

    return (
        f"{nombre:22s} zR{z['Ring']:+5.1f} zP{z['Pinky']:+6.1f} | "
        f"fondo MR {pc('MR_punta')}/{pc('MR_medio')}/{pc('MR_base')} "
        f"RP {pc('RP_punta')}/{pc('RP_medio')}/{pc('RP_base')} | "
        f"costura MR {an['MR_medio_c']:.3f} RP {an['RP_medio_c']:.3f} | "
        f"aplastado={an['aplastado'] if an['aplastado'] is None else round(an['aplastado'], 3)} "
        f"| pinza={m['pinza']:.3f}"
    )


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    fichas = []
    with sync_playwright() as p:
        browser, page = abrir(p)
        page.set_viewport_size({"width": 900, "height": 950})
        time.sleep(0.5)
        preparar(page)
        for nombre, nud, cierre, largo in CASOS:
            clave = nombre.split()[0]
            if nud is None:
                z = {"Middle": 0.0, "Ring": 0.0, "Pinky": 0.0}
                page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", BASE)
            else:
                z = paralelos(page, nud, cierre, largo)
                page.evaluate(
                    "(x) => window.__LSM_CONTROLLER__.applyTestPose(x)",
                    pose(nud, z["Middle"], z["Ring"], z["Pinky"], largo),
                )
            time.sleep(0.2)
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
            an = analizar(Image.open(entera), page.evaluate(PIXELES_JS))
            img = Image.open(entera)
            zoom = OUT / f"{clave}_zoom.png"
            img.crop(an["recorte"]).save(zoom)
            fichas.append((nombre, zoom))
            print(fila_informe(nombre, z, m, an))
        browser.close()

    print("hoja:", hoja(fichas, OUT / "_zoom.png", cols=4, cell=330))


if __name__ == "__main__":
    main()
