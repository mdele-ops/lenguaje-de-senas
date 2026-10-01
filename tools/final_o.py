"""Escribe en el catalogo la O corregida y deja el antes/despues para revisarla.

Que estaba mal y que cambia:

1. El aro no cerraba. La pose anterior era `curl` y nada mas (0.6 en los cuatro
   dedos, 0.55 en el pulgar): la yema del pulgar se quedaba a 0.40 largos de
   palma de la del indice, con el pulgar apuntando al frente. Eso no es una O,
   es una garra; de hecho se parecia mas a la C que a la O. Ahora el pulgar
   sube a buscar las yemas y el contacto queda en 0.09.

   Como en la E, la orientacion del pulgar no se saca de `curl`/`aside`: hay
   que girar la base (Thumb1), que apunta el dedo entero sin doblarlo.

2. Los cuatro dedos doblaban distinto. Con el mismo `curl` la ultima falange
   iba de 14 grados en el anular a 41 en el indice, porque el reposo del .glb
   no es simetrico, y el arco salia escalonado. El retoque por falange
   (calibra_o.py) los deja en 33.5 los cuatro.

3. La mano no se veia. El agujero de la O vive en el plano largo-frente de la
   palma, asi que con la mano de frente se presentaba de canto: el area del
   aro en la camara de la app era 0.02. Girando la muneca 70 grados -la misma
   idea que en la C- sube a 0.18 y la letra se lee de un vistazo.
"""
import json
from pathlib import Path

from pose_lab_e import ARM, BONES, FINGERS, T1, T2, T3
from pose_o import dedos, juntar, pulgar
from retrato_o import ARM_Z, CATALOGO, pose_catalogo, retratar

ROOT = Path(__file__).resolve().parents[1]
AFINADA = ROOT / "tools" / "screenshots" / "afina_o.json"
OUT = ROOT / "tools" / "screenshots" / "final_o"

MUNECA = {"y": 70}

DESCRIPCION = (
    "Mano de perfil delante del pecho, palma hacia el costado: los cuatro "
    "dedos, juntos y curvados por igual, bajan formando el arco de arriba y el "
    "pulgar sube a su encuentro hasta que las yemas se tocan, dejando un hueco "
    "redondo con la forma de la letra O."
)

ORDEN = ("thumb", "index", "middle", "ring", "pinky", "muneca", "extra")
MINIMO = 1.5  # grados: por debajo de esto el retoque no se ve y solo ensucia

CADENA = [T1, T2, T3] + [BONES[f][j] for f in FINGERS for j in (0, 1, 2)] + [ARM]


def grados(v):
    v = round(v, 1)
    return int(v) if v == int(v) else v


def limpiar(pz):
    """Deja la pose legible: orden anatomico, sin retoques irrelevantes."""
    rango = {n: i for i, n in enumerate(CADENA)}
    extra = {}
    for hueso in sorted(pz.get("extra", {}), key=lambda n: (rango.get(n, 99), n)):
        rot = {
            eje: grados(g)
            for eje, g in pz["extra"][hueso].items()
            if abs(g) >= MINIMO
        }
        if rot:
            extra[hueso] = rot

    out = {}
    for clave in ORDEN:
        if clave == "extra":
            if extra:
                out["extra"] = extra
        elif clave == "muneca":
            if pz.get("muneca"):
                out["muneca"] = {k: grados(v) for k, v in pz["muneca"].items()}
        elif clave in pz:
            out[clave] = {
                k: (grados(v) if k == "spread" else round(v, 3))
                for k, v in pz[clave].items()
            }
    return out


def construir():
    d = json.loads(AFINADA.read_text("utf-8"))
    kd, kp = d["dedos"], d["pulgar"]
    return limpiar(
        juntar(
            dedos(**kd),
            pulgar(
                kp["curl"], kp["aside"],
                t1={"x": kp["t1x"], "y": kp["t1y"], "z": kp["t1z"]},
                t2x=kp["t2x"], t3x=kp["t3x"],
            ),
            muneca=MUNECA,
            arm_z=ARM_Z,
        )
    )


def main():
    anterior = pose_catalogo()
    nueva = construir()
    retratar([("1_ANTES", anterior), ("2_DESPUES", nueva)], OUT, cols=4, cell=340)

    cat = json.loads(CATALOGO.read_text("utf-8"))
    sena = next(s for s in cat["senas"] if s["letra"] == "O")
    sena["pose"] = nueva
    sena["descripcion"] = DESCRIPCION
    partes = cat["version"].split(".")
    partes[-1] = str(int(partes[-1]) + 1)
    cat["version"] = ".".join(partes)
    CATALOGO.write_text(
        json.dumps(cat, ensure_ascii=False, indent=2) + "\n", "utf-8"
    )
    print("\ncatalogo ->", CATALOGO, "version", cat["version"])

    (OUT / "_pose.json").write_text(
        json.dumps({"antes": anterior, "despues": nueva}, indent=2), "utf-8"
    )


if __name__ == "__main__":
    main()
