"""R lab 3: busca el cruce de indice y medio con la geometria, no a ojo.

Del lab 1 salieron los ejes utiles del nudillo en este rig:
  z  mueve el dedo de lado dentro del plano de la palma (+z hacia el menique)
  x  lo flexiona; +x lo lleva hacia la palma, o sea hacia el espectador
  y  lo tuerce sobre su propio eje

Y del lab 2, que la camara ve la PALMA, con el indice a la izquierda de la
pantalla y el menique a la derecha. El cruce lateral es entonces indice +z (se
va a la derecha) y medio -z (se va a la izquierda).

Quien pasa por delante lo decide la lamina oficial (assets/Abecedario...), que
esta dibujada "vista por el espectador": ampliando las dos yemas se ve que la
de la DERECHA es mas ancha, mas alta y tapa a la otra. Esa yema de la derecha
es la del INDICE, porque el indice sale del nudillo de la izquierda y al
cruzarse acaba a la derecha. O sea que en la R monta por delante el INDICE y el
medio es el que queda detras.

El primer intento cruzo los dedos girando solo los nudillos, y de perfil salia
una V: dos varillas rigidas que se separan segun suben. En la lamina los dedos
van montados uno sobre otro y PARALELOS, a un grosor de dedo de distancia. Por
eso el adelanto se hace en dos tramos: el nudillo saca el dedo hacia la palma y
la falange media lo vuelve a enderezar, que es el escalon que deja los dos
dedos paralelos pero a distinta profundidad.

  abanico  cuanto crece la diferencia de profundidad de la falange media a la
           yema. ~0 = dedos paralelos (lo que se busca); grande = la V.
"""
import itertools
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from pose_lab_e import free_camera
from pose_lab_r import MEASURE_JS, pose_r
import search_e9 as se9
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
SALIDA = ROOT / "tools" / "screenshots" / "search_r.json"

se9.URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=r3"

# Lo que tiene que cumplir la pose para que se lea una R y no una U ni una V.
#   cruce      las yemas cambiadas de lado, en anchos de nudillo
#   crucePip   ~0: el cruce cae a la altura de la falange media, como la lamina
#   gap        se rozan pero no se atraviesan (un dedo mide ~0.18 de palma)
#   frenteMed  positivo = el medio queda detras y el indice monta por delante,
#              separados un grosor de dedo, no mas
#   abanico    ~0: montados y paralelos, no abiertos en V vistos de perfil
#   sepYemas   las dos yemas quedan juntas arriba
BANDAS = {
    # el barrido del lab 6 enseno que por debajo de cruce ~0.9 la silueta sigue
    # leyendose como una U: los dos dedos se tapan y no se ve la equis
    "cruce": (0.95, 1.55),
    "crucePip": (-0.35, 0.20),
    "gap": (0.155, 0.300),
    "frenteMed": (0.16, 0.34),
    "abanico": (-0.10, 0.10),
    # en la lamina las dos yemas quedan juntas arriba; sin apretar esta banda
    # los dedos se cruzan pero luego se abren en V
    "sepYemas": (0.16, 0.32),
    "altIdx": (0.70, 1.10),
    "altMed": (0.70, 1.10),
    "vertIdx": (0.88, 1.00),
    "vertMed": (0.88, 1.00),
}
PESOS = {
    "cruce": 6.0,
    "crucePip": 2.0,
    "gap": 10.0,
    "frenteMed": 5.0,
    "abanico": 8.0,
    "sepYemas": 3.0,
    "altIdx": 2.5,
    "altMed": 2.5,
    "vertIdx": 3.0,
    "vertMed": 3.0,
}


def banda(v, lo, hi):
    if v < lo:
        return lo - v
    if v > hi:
        return v - hi
    return 0.0


def puntuar(m, claves=None):
    """Menor es mejor. `claves` limita la cuenta a lo que toca cada fase."""
    total = 0.0
    for k in claves or BANDAS:
        lo, hi = BANDAS[k]
        total += PESOS[k] * banda(m[k], lo, hi)
    return total


def cruzar(
    iz, mz, mx=0, ix=0, ix2=0, mx2=0, iz2=0, mz2=0, ix3=0, mx3=0,
    ity=0, mty=0, **kw
):
    """Arma la R: cruce lateral en z, adelanto del indice en x y reenderezado.

    Los sufijos 2 y 3 son la falange media y la distal. `iz2`/`mz2` cierran las
    yemas otra vez una sobre otra despues del cruce: sin ellos los dos dedos se
    abren en V por encima del cruce y en la lamina van juntos.
    """
    idx = {0: {"x": ix, "y": ity, "z": iz}}
    med = {0: {"x": mx, "y": mty, "z": mz}}
    if ix2 or mx2 or iz2 or mz2:
        idx[1] = {"x": ix2, "z": iz2}
        med[1] = {"x": mx2, "z": mz2}
    if ix3 or mx3:
        idx[2] = {"x": ix3}
        med[2] = {"x": mx3}
    return pose_r(idx=idx, med=med, **kw)


def linea(nombre, m, s):
    return (
        f"{nombre:34s} s={s:6.3f} cruce={m['cruce']:+5.2f}/{m['crucePip']:+5.2f} "
        f"gap={m['gap']:.3f} frente={m['frenteMed']:+5.2f} "
        f"aban={m['abanico']:+5.2f} yemas={m['sepYemas']:.2f} "
        f"vert={m['vertIdx']:.2f}/{m['vertMed']:.2f}"
    )


def main():
    with sync_playwright() as p:
        browser, page = abrir(p)
        free_camera(page)

        def medir(pose):
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
            return page.evaluate(MEASURE_JS)

        catalogo = json.loads((ROOT / "data" / "catalogo-lsm.json").read_text("utf-8"))
        actual = next(s for s in catalogo["senas"] if s["letra"] == "R")["pose"]
        m = medir(actual)
        print("R del catalogo (para comparar)")
        print(" ", linea("R_actual", m, puntuar(m)), "\n")

        # ---- Fase 1: cruce lateral + escalon de profundidad ------------------
        rej1 = list(
            itertools.product(
                (18, 22, 26),              # iz: indice a la derecha
                (-18, -22, -26),           # mz: medio a la izquierda
                (26, 32, 38, 44),          # ix: nudillo del indice a la palma
                (-20, -30, -40),           # ix2: falange media lo endereza
                (0, -10, -20, -30),        # iz2: yema del indice de vuelta
                (0, 10, 20, 30),           # mz2: y la del medio
            )
        )
        print(f"Fase 1: {len(rej1)} combinaciones")
        r1 = []
        for iz, mz, ix, ix2, iz2, mz2 in rej1:
            mm = medir(cruzar(iz, mz, ix=ix, ix2=ix2, iz2=iz2, mz2=mz2))
            r1.append((puntuar(mm), (iz, mz, ix, ix2, iz2, mz2), mm))
        r1.sort(key=lambda t: t[0])
        for s, k, mm in r1[:12]:
            print(
                " ",
                linea(f"iz{k[0]} mz{k[1]} ix{k[2]}/{k[3]} z2:{k[4]}/{k[5]}", mm, s),
            )
        print()

        mejores = [k for _, k, _ in r1[:6]]

        # ---- Fase 2: torsion, para que los dedos se nesten en vez de chocar --
        rej2 = list(itertools.product((-16, -8, 0, 8, 16), (-16, -8, 0, 8, 16)))
        print(f"Fase 2: {len(rej2)} torsiones x {len(mejores)} cruces")
        r2 = []
        for iz, mz, ix, ix2, iz2, mz2 in mejores:
            for ity, mty in rej2:
                pose = cruzar(
                    iz, mz, ix=ix, ix2=ix2, iz2=iz2, mz2=mz2,
                    ity=ity, mty=mty,
                )
                mm = medir(pose)
                r2.append(
                    (puntuar(mm), ((iz, mz, ix, ix2, iz2, mz2), (ity, mty)), mm)
                )
        r2.sort(key=lambda t: t[0])
        print("MEJORES COMBINADAS")
        for s, k, mm in r2[:15]:
            a, b = k
            nombre = (
                f"iz{a[0]} mz{a[1]} ix{a[2]}/{a[3]} z2:{a[4]}/{a[5]} "
                f"ty{b[0]}/{b[1]}"
            )
            print(" ", linea(nombre, mm, s))

        browser.close()

    SALIDA.write_text(
        json.dumps(
            [
                {
                    "score": s,
                    "kw": dict(
                        iz=k[0][0], mz=k[0][1], ix=k[0][2], ix2=k[0][3],
                        iz2=k[0][4], mz2=k[0][5], ity=k[1][0], mty=k[1][1],
                    ),
                    "metricas": mm,
                }
                for s, k, mm in r2[:40]
            ],
            indent=2,
        ),
        "utf-8",
    )
    print("\nTop 40 ->", SALIDA)


if __name__ == "__main__":
    main()
