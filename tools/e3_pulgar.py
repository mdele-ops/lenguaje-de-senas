"""Busca los angulos del pulgar de la E contra lo que se mide en la foto.

Las perillas del pulgar (curl, aside y los extras de Thumb1/2/3) mueven la yema
de forma muy acoplada: cualquier giro que la baja tambien la manda a cruzar la
palma. Barrer eje por eje no encuentra la combinacion, asi que se tiran dardos
al azar en las siete perillas y se puntua contra la foto.

Objetivo leido en E_usuario3_big.png, que si ensena la muneca y por tanto deja
fijar la escala (palma = muneca -> nudillo del medio = 440 px; fila de nudillos
= alto 1.00 en y=110; abanico indice-menique = 215 px):

    nudillo IP  alto +0.34  ancho +0.05  frente +0.15
    yema        alto +0.46  ancho +0.30  frente +0.30

O sea: el pulgar va tumbado y BAJO sobre la palma, apenas cruzando la columna
del indice, apuntando hacia arriba y hacia el menique, y abultando por delante
de la palma. Nada de subir de pie al lado de los dedos (que es lo que hacia el
catalogo: la yema le quedaba en alto 1.01, a la altura de los nudillos).
"""
import random
import sys

from playwright.sync_api import sync_playwright

from e2_medidas import MED_JS
from e3_lab import pose_e
from lab_e2 import abrir, aplicar, preparar

DEDOS = {"nudillos": 0.45}

OBJETIVO = {
    "tAlto3": 0.34,
    "tAncho3": 0.05,
    "tFrente3": 0.15,
    "tAlto4": 0.46,
    "tAncho4": 0.30,
    "tFrente4": 0.30,
}
# El frente pesa como el alto: si se deja flojo, la busqueda hace trampa y saca
# el pulgar apuntando a la camara (frente +0.93). Asi proyectado cae justo donde
# lo pide la foto, pero de perfil es un pulgar tieso saliendo del puno.
PESOS = {
    "tAlto3": 3.0,
    "tAncho3": 2.0,
    "tFrente3": 3.0,
    "tAlto4": 3.0,
    "tAncho4": 2.0,
    "tFrente4": 3.0,
}

# `aside` y el extra `y` de Thumb1 giran el mismo hueso sobre el mismo eje, asi
# que sobra uno: se deja solo el extra y se buscan seis perillas en vez de siete.
RANGOS = {
    "tcurl": (0.20, 1.00),
    "t1x": (-40, 100),
    "t1y": (-90, 50),
    "t1z": (-40, 110),
    "t2x": (-20, 80),
    "t3x": (-20, 80),
}


def completar(p):
    return dict(p, taside=0.0)


def pose(p):
    return pose_e(
        tcurl=p["tcurl"],
        taside=0.0,
        t1=(p["t1x"], p["t1y"], p["t1z"]),
        t2x=p["t2x"],
        t3x=p["t3x"],
        **DEDOS,
    )


def puntuar(m):
    coste = 0.0
    for clave, objetivo in OBJETIVO.items():
        coste += PESOS[clave] * abs(m[clave] - objetivo)
    # La yema del pulgar no puede quedar por detras de la del indice: ahi el
    # pulgar se mete dentro de la malla de la palma y el render sale sucio.
    if m["tFrente4"] < 0.10:
        coste += 4.0 * (0.10 - m["tFrente4"])
    return coste


def linea(nombre, m, coste):
    return (
        f"{coste:6.3f}  {nombre:34s} "
        f"t3={m['tAlto3']:+.2f}/{m['tAncho3']:+.2f}/{m['tFrente3']:+.2f} "
        f"t4={m['tAlto4']:+.2f}/{m['tAncho4']:+.2f}/{m['tFrente4']:+.2f} "
        f"incl={m['pTInclina']:+4.0f} toca={m['tocaDedos']:.2f} ip={m['ipAng']:.0f}"
    )


def etiqueta(p):
    return (
        f"c{p['tcurl']:.2f} t1 {p['t1x']:+.0f}/{p['t1y']:+.0f}/{p['t1z']:+.0f} "
        f"t2{p['t2x']:+.0f} t3{p['t3x']:+.0f}"
    )


def dardo(rnd, centro=None, radio=1.0):
    p = {}
    for clave, (lo, hi) in RANGOS.items():
        if centro is None:
            p[clave] = rnd.uniform(lo, hi)
        else:
            ancho = (hi - lo) * radio
            p[clave] = min(hi, max(lo, rnd.gauss(centro[clave], ancho / 4)))
    return p


def main():
    tiros = int(sys.argv[1]) if len(sys.argv) > 1 else 600
    rnd = random.Random(7)
    mejores = []

    with sync_playwright() as p:
        browser, page = abrir(p)
        preparar(page)

        def evaluar(cand):
            aplicar(page, pose(cand), espera=0.12)
            m = page.evaluate(MED_JS)
            if "error" in m or "sTBajo" not in m:
                return None
            return m

        for i in range(tiros):
            cand = dardo(rnd)
            m = evaluar(cand)
            if m is None:
                continue
            mejores.append((puntuar(m), cand, m))
            if (i + 1) % 100 == 0:
                mejores.sort(key=lambda x: x[0])
                mejores = mejores[:40]
                print(f"  ({i+1} tiros, mejor {mejores[0][0]:.3f})")

        # segunda vuelta: apretar alrededor de los cinco mejores
        mejores.sort(key=lambda x: x[0])
        semillas = [c for _, c, _ in mejores[:5]]
        for semilla in semillas:
            for _ in range(60):
                cand = dardo(rnd, centro=semilla, radio=0.25)
                m = evaluar(cand)
                if m is not None:
                    mejores.append((puntuar(m), cand, m))

        mejores.sort(key=lambda x: x[0])
        browser.close()

    print()
    for coste, cand, m in mejores[:15]:
        print(linea(etiqueta(cand), m, coste))
    print()
    print("mejor:", etiqueta(mejores[0][1]))
    print("repr :", mejores[0][1])


if __name__ == "__main__":
    main()
