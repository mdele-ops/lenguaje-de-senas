"""Barrido de medidas de la E: aplica muchas poses y solo mide, sin retratar.

Retratar cada candidata cuesta ~3 s de encuadre por vista, asi que para buscar
la altura de las yemas y el sitio del pulgar conviene medir a ciegas primero y
dejar las capturas para las dos o tres que sobrevivan.
"""
from playwright.sync_api import sync_playwright

from e2_medidas import MED_JS
from e3_lab import pose_e
from lab_e2 import abrir, aplicar, preparar

# Objetivo leido en la foto del usuario (E_usuario3_mano.png, 630x900), con la
# palma = muneca -> nudillo del medio:
#   yemas    alto ~ +0.86  (0.14 por debajo de la fila de nudillos), las cuatro
#                          a la misma altura
#   yemas    frente ~ +0.12, apoyadas en la palma
#   pulgar   yema alto ~ +0.48, ancho ~ +0.16 (columna del indice/medio),
#            frente positivo: el pulgar abulta por delante de la palma
#   pulgar   nudillo IP alto ~ +0.38, ancho ~ 0.00
OBJETIVO = {
    "alto": 0.86,
    "frente": 0.12,
    "tAlto4": 0.48,
    "tAncho4": 0.16,
    "tAlto3": 0.38,
    "tAncho3": 0.00,
}


def linea(nombre, m):
    return (
        f"{nombre:26s} yalto={fmt(m['alto'])} yfr={fmt(m['frente'])} "
        f"D={m['altoDisp']:.2f} | t4={m['tAlto4']:+.2f}/{m['tAncho4']:+.2f}/"
        f"{m['tFrente4']:+.2f} t3={m['tAlto3']:+.2f}/{m['tAncho3']:+.2f} "
        f"| baja={m['pBajaYema']:+.2f} tBajo={m['pTBajoYemas']:+.2f} "
        f"incl={m['pTInclina']:+.0f} toca={m['tocaDedos']:.2f}"
    )


def linea_dedos(nombre, m):
    return (
        f"{nombre:28s} yalto={fmt(m['alto'])} D={m['altoDisp']:.2f} "
        f"nud={fmt(m['knuAlto'])} rel={fmt(m['yemaRel'])} Drel={m['yemaRelDisp']:.2f} "
        f"yfr={fmt(m['frente'])} gap={fmt(m['gaps'])}"
    )


def linea_pulgar(nombre, m):
    return (
        f"{nombre:30s} t2={m['tAlto2']:+.2f}/{m['tAncho2']:+.2f}/{m['tFrente2']:+.2f} "
        f"t3={m['tAlto3']:+.2f}/{m['tAncho3']:+.2f}/{m['tFrente3']:+.2f} "
        f"t4={m['tAlto4']:+.2f}/{m['tAncho4']:+.2f}/{m['tFrente4']:+.2f} "
        f"| incl={m['pTInclina']:+.0f} tBajo={m['pTBajoYemas']:+.2f} "
        f"toca={m['tocaDedos']:.2f} ip={m['ipAng']:.0f}"
    )


def fmt(v, dec=2):
    return "[" + " ".join(f"{x:+.{dec}f}" for x in v) + "]"


def correr(candidatas, mostrar=linea):
    """candidatas: lista de (nombre, pose). Devuelve {nombre: medidas}."""
    res = {}
    with sync_playwright() as p:
        browser, page = abrir(p)
        preparar(page)
        for nombre, pose in candidatas:
            aplicar(page, pose, espera=0.25)
            m = page.evaluate(MED_JS)
            if "error" in m:
                print(f"{nombre:26s} ERROR {m['error']}")
                continue
            res[nombre] = m
            print(mostrar(nombre, m))
        browser.close()
    return res


def etapa_dedos():
    """Nivelar las cuatro yemas: raiz de los nudillos y largo de las falanges."""
    cand = [("catalogo", pose_e())]
    for nud in (0.0, 0.2, 0.35):
        for pk in (1.0, 1.12, 1.24):
            for rg in (1.0, 1.08):
                cand.append(
                    (
                        f"nud{nud:.2f} pk{pk:.2f} rg{rg:.2f}",
                        pose_e(nudillos=nud, largo={"pinky": pk, "ring": rg}),
                    )
                )
    correr(cand, mostrar=linea_dedos)


def etapa_pulgar():
    """Bajar la yema del pulgar hasta media palma, en la columna del indice."""
    base = {"nudillos": 0.2, "largo": {"pinky": 1.12}}
    cand = [("catalogo", pose_e(**base))]
    for t1z in (30, 50, 70):
        for t1y in (-60, -35, -10):
            for t1x in (20, 45, 70):
                for t2x in (10, 30, 50):
                    cand.append(
                        (
                            f"x{t1x} y{t1y} z{t1z} t2{t2x}",
                            pose_e(t1=(t1x, t1y, t1z), t2x=t2x, **base),
                        )
                    )
    correr(cand, mostrar=linea_pulgar)


ETAPAS = {"dedos": etapa_dedos, "pulgar": etapa_pulgar}


def main():
    import sys

    etapa = sys.argv[1] if len(sys.argv) > 1 else "dedos"
    ETAPAS[etapa]()


if __name__ == "__main__":
    main()
