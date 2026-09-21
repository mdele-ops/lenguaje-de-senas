"""Cuanto asoma el pulgar POR ENCIMA del puno, medido en la silueta del render.

Este es el error que traia la busqueda de la T desde el principio. `camCima`
compara el hueso de la yema con el hueso mas alto de los dedos, y los huesos no
estan a la misma profundidad dentro de la carne: el de la yema del pulgar cae
casi en la punta, mientras que los de los dedos van por el centro del dedo, o
sea medio dedo por debajo de su contorno. Con camCima +0.116 el numero decia
que el pulgar asomaba un buen trozo y en el render la yema quedaba a ras.

La lamina, en cambio, esta medida sobre CARNE: es una foto, ahi no hay huesos.
Para poder comparar las dos hay que medir carne en las dos, y eso es lo que
hace este modulo: saca la silueta de la mano del render (la piel se separa bien
del fondo: chaqueta gris neutra, chaleco azul y fondo oscuro) y devuelve

  asoma   cuanto sube el punto mas alto de la mano por encima del punto mas
          alto del puno SIN pulgar, en anchos de puno. En la lamina vale ~0.09.
  ancho   lo ancho que se ve el pulgar, en anchos de puno. Sirve para no dar
          por buena una pose donde el pulgar se lee como un quinto dedo.

Las dos necesitan una captura de referencia del MISMO puno con el pulgar
apartado, que es la unica forma de saber donde acaba el puno y donde empieza el
pulgar sin ponerse a segmentar dedos.
"""
import numpy as np
from PIL import Image

# La piel del modelo es clara y calida; el fondo no tiene nada asi. La chaqueta
# es gris neutra (R~G~B) y el chaleco azul (B>R), asi que pedir que el rojo
# gane al azul con holgura basta para quedarse con la mano.
MIN_R = 150
MIN_RB = 22
MIN_RG = 4


def piel(im):
    a = np.asarray(im.convert("RGB")).astype(np.int16)
    r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    return (r > MIN_R) & (r - b > MIN_RB) & (r - g > MIN_RG)


def perfil(mask):
    """Fila mas alta con piel en cada columna; -1 si la columna esta vacia."""
    hay = mask.any(axis=0)
    top = np.argmax(mask, axis=0)
    return np.where(hay, top, -1)


def _cima(mask, x0, x1):
    """(fila, columna) del punto mas alto de la piel entre x0 y x1."""
    p = perfil(mask)[x0:x1]
    hay = p >= 0
    if not hay.any():
        return None, None
    fila = int(p[hay].min())
    cols = np.nonzero(hay & (p == fila))[0]
    return fila, int(x0 + cols.mean())


def mide(fondo, cand, x0, x1, ancho_puno):
    """Compara la silueta de la pose con la del mismo puno sin pulgar.

    `x0`/`x1` acotan las columnas del puno (fuera de ahi esta el brazo, que
    tambien es piel y tiraria las medidas). `ancho_puno` va en pixeles de la
    imagen, para devolverlo todo en anchos de puno como la lamina.
    """
    mf, mc = piel(fondo), piel(cand)
    cf, _ = _cima(mf, x0, x1)
    cc, xc = _cima(mc, x0, x1)
    if cf is None or cc is None:
        return None

    # Columnas donde la pose sube por encima del contorno del puno: eso, y solo
    # eso, es pulgar que se ve asomar.
    pf, pc = perfil(mf)[x0:x1], perfil(mc)[x0:x1]
    sube = (pc >= 0) & ((pf < 0) | (pc < pf - 2))
    return {
        "asoma": (cf - cc) / ancho_puno,
        "ancho": int(sube.sum()) / ancho_puno,
        "cimaPuno": cf,
        "cimaMano": cc,
        "xCima": xc,
    }


def desde_rutas(ruta_fondo, ruta_cand, x0, x1, ancho_puno):
    return mide(Image.open(ruta_fondo), Image.open(ruta_cand), x0, x1, ancho_puno)
