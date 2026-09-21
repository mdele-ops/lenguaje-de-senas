"""Retrata la O afinada: contra la del catalogo y con varios giros de muneca.

El giro no cambia la forma de la mano, pero si lo que se ve: el aro de la O
vive en el plano largo-frente de la palma, asi que con la mano de frente se
presenta de canto y el agujero desaparece. Aqui se prueban varios angulos para
elegir desde que orientacion se lee mejor en la camara de la app.
"""
import json
import sys
from pathlib import Path

from pose_o import dedos, juntar, pulgar
from retrato_o import ARM_Z, MUNECA, pose_catalogo, retratar

ROOT = Path(__file__).resolve().parents[1]
AFINADA = ROOT / "tools" / "screenshots" / "afina_o.json"
OUT = ROOT / "tools" / "screenshots" / "mira_o"

GIROS = (0, 30, 50, 70, 90, 110)


def construir(kd, kp, muneca=MUNECA):
    return juntar(
        dedos(**kd),
        pulgar(
            kp["curl"], kp["aside"],
            t1={"x": kp["t1x"], "y": kp["t1y"], "z": kp["t1z"]},
            t2x=kp["t2x"], t3x=kp["t3x"],
        ),
        muneca=muneca,
        arm_z=ARM_Z,
    )


def main():
    d = json.loads(AFINADA.read_text("utf-8"))
    if "--giros" in sys.argv:
        casos = [
            (f"y{g:03d}", construir(d["dedos"], d["pulgar"], muneca={"y": g}))
            for g in GIROS
        ]
    else:
        variantes = json.loads(
            (ROOT / "tools" / "screenshots" / "variantes_o" / "_recetas.json")
            .read_text("utf-8")
        )
        casos = [
            ("0_catalogo", pose_catalogo()),
            ("1_afinada", construir(d["dedos"], d["pulgar"])),
        ] + [
            (f"2_{n}", construir(r["dedos"], r["pulgar"]))
            for n, r in variantes.items()
            if n in ("B_media", "C_cerrada")
        ]
    retratar(casos, OUT, cols=4, cell=320, huesos="--huesos" in sys.argv)


if __name__ == "__main__":
    main()
