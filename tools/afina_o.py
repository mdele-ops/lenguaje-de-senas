"""Afina la O por descenso de coordenadas, alternando dedos y pulgar.

La rejilla de busca_o.py dejaba el optimo pegado al borde en cuatro de los seis
mandos del pulgar: la rejilla era demasiado estrecha y demasiado gruesa a la
vez. Aqui cada mando se recorre entero, de uno en uno, y se repite la vuelta
hasta que nada mejora.

Sigue valiendo el truco de medir dedos y pulgar por separado, asi que cada
combinacion nueva cuesta como mucho un renderizado (y ninguno si ya se midio
esa mitad antes).
"""
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from calibra_o import calibrar, limpiar, objetivo_medio
from medida_o import HUESOS, MARCO_JS, detalle, linea, metricas, puntuar
from pose_o import dedos, pulgar
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "afina_o.json"

DEDO_BONES = tuple(n.split("_")[0] for n in HUESOS if not n.startswith("Thumb"))
PULGAR_BONES = tuple(n.split("_")[0] for n in HUESOS if n.startswith("Thumb"))


def escala(lo, hi, paso):
    n = int(round((hi - lo) / paso))
    return [round(lo + i * paso, 3) for i in range(n + 1)]


MANDOS_DEDOS = {
    "curl": escala(0.40, 0.95, 0.025),
    "mcp": escala(-20, 30, 2),
    "pip": escala(-20, 30, 2),
    "dip": escala(-30, 20, 2),
    "fan": escala(-16, 16, 2),
}

MANDOS_PULGAR = {
    "curl": escala(0.10, 0.95, 0.025),
    "aside": escala(-0.6, 1.3, 0.05),
    "t1x": escala(-40, 70, 5),
    "t1y": escala(-60, 70, 5),
    "t1z": escala(-40, 100, 5),
    "t2x": escala(-40, 70, 5),
    "t3x": escala(-40, 70, 5),
}

# Arranca en la variante que mejor se veia en la hoja de contactos
# (variantes_o.py, "C_cerrada": arco 66/66/34), no en el centro de la rejilla.
SEMILLA_DEDOS = {"curl": 0.70, "mcp": 8, "pip": 4, "dip": -6, "fan": -2}
SEMILLA_PULGAR = {
    "curl": 0.50, "aside": 0.5, "t1x": 0, "t1y": 20, "t1z": 20, "t2x": 0, "t3x": 0,
}


class Medidor:
    """Mide una mitad de la pose y se acuerda de lo ya medido."""

    def __init__(self, page):
        self.page = page
        self.cache = {}
        self.rondas = 0

    def _marco(self, pose, huesos):
        self.page.evaluate(
            "(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose
        )
        marco = self.page.evaluate(MARCO_JS)
        if "error" in marco:
            raise RuntimeError(marco["error"])
        self.rondas += 1
        return {h: marco[h] for h in huesos}

    def dedos(self, kw):
        clave = "d" + json.dumps(kw, sort_keys=True)
        if clave not in self.cache:
            self.cache[clave] = self._marco(dedos(**kw), DEDO_BONES)
        return self.cache[clave]

    def pulgar(self, kw):
        clave = "t" + json.dumps(kw, sort_keys=True)
        if clave not in self.cache:
            self.cache[clave] = self._marco(
                pulgar(
                    kw["curl"], kw["aside"],
                    t1={"x": kw["t1x"], "y": kw["t1y"], "z": kw["t1z"]},
                    t2x=kw["t2x"], t3x=kw["t3x"],
                ),
                PULGAR_BONES,
            )
        return self.cache[clave]

    def evaluar(self, kd, kp):
        o = metricas({**self.dedos(kd), **self.pulgar(kp)})
        return puntuar(o), o


def descenso(med, kd, kp, cual, mandos, vueltas=3):
    """Recorre entero cada mando, de uno en uno, y se queda con lo mejor."""
    activo = dict(kd if cual == "d" else kp)
    mejor = med.evaluar(kd, kp)[0]
    for _ in range(vueltas):
        cambio = False
        for mando, valores in mandos.items():
            base = activo[mando]
            for v in valores:
                if v == base:
                    continue
                prueba = dict(activo, **{mando: v})
                s = med.evaluar(prueba, kp)[0] if cual == "d" else med.evaluar(kd, prueba)[0]
                if s < mejor - 1e-9:
                    mejor, activo, cambio = s, prueba, True
            if cual == "d":
                kd = activo
            else:
                kp = activo
        if not cambio:
            break
    return kd, kp, mejor


def main():
    t0 = time.time()
    with sync_playwright() as p:
        browser, page = abrir(p)
        med = Medidor(page)
        kd, kp = dict(SEMILLA_DEDOS), dict(SEMILLA_PULGAR)
        score = med.evaluar(kd, kp)[0]
        print(f"semilla   score={score:6.3f}")

        for vuelta in range(1, 5):
            kd, kp, score = descenso(med, kd, kp, "t", MANDOS_PULGAR)
            print(f"vuelta {vuelta} pulgar score={score:6.3f}  {kp}", flush=True)
            kd, kp, nuevo = descenso(med, kd, kp, "d", MANDOS_DEDOS)
            print(f"         dedos  score={nuevo:6.3f}  {kd}", flush=True)
            if nuevo > score - 1e-6:
                score = nuevo
                break
            score = nuevo

        # El arco ya es el bueno, pero cada dedo lo cumple de una forma; esto
        # lo reparte igual entre los cuatro sin cambiar la media.
        o = metricas({**med.dedos(kd), **med.pulgar(kp)})
        corr, _ = calibrar(
            lambda kw: metricas({**med.dedos(kw), **med.pulgar(kp)}),
            kd,
            objetivo_medio(o),
        )
        kd = dict(kd, corr=limpiar(corr))
        score, o = med.evaluar(kd, kp)
        print(f"calibrada      score={score:6.3f}", flush=True)

        # el pulgar tiene que volver a buscar las yemas, que se han movido
        kd, kp, score = descenso(med, kd, kp, "t", MANDOS_PULGAR)
        print(f"remate pulgar  score={score:6.3f}  {kp}", flush=True)

        score, o = med.evaluar(kd, kp)
        browser.close()

    print(f"\n{linea('afinada', o, score)}")
    print(detalle(o))
    print(f"\n{med.rondas} medidas en {time.time()-t0:.0f}s")
    OUT.write_text(
        json.dumps({"score": score, "dedos": kd, "pulgar": kp, "medidas": o}, indent=2),
        "utf-8",
    )
    print("->", OUT)


if __name__ == "__main__":
    main()
