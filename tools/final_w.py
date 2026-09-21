"""W final: tridente cerrado, huecos iguales, pulgar sobre el meñique.

La W del catalogo usaba index -14 / ring +20: en pantalla el indice se iba
a ~39 deg (mas abierto que la V) y se leia como abanico. La foto pide tres
palitos verticales con un hueco claro pero modesto entre vecinos.

Se guarda index -6 / ring +12: en 3D los dos huecos quedan iguales
(~15 deg, sep 0.42/0.45). El pulgar es el de la U con Thumb1.z=50 para
alcanzar el meñique.
"""
import json
from pathlib import Path

from pose_lab_e import T1, T2
from pose_lab_w import pose_w

ROOT = Path(__file__).resolve().parents[1]
CATALOGO = ROOT / "data" / "catalogo-lsm.json"

POSE = pose_w(
    iz=-6,
    mz=0,
    rz=12,
    thumb={T1: {"y": -30, "z": 50}, T2: {"x": 60}},
)

DESCRIPCION = (
    "Índice, medio y anular estirados hacia arriba, con un hueco visible "
    "entre cada uno, como los tres palitos de la W (sin abrirlos en abanico). "
    "El meñique se recoge contra la palma y el pulgar queda tumbado encima, "
    "con la yema apoyada sobre el meñique."
)


def guardar(pose):
    datos = json.loads(CATALOGO.read_text(encoding="utf-8"))
    sena = next(s for s in datos["senas"] if s["letra"] == "W")
    sena["pose"] = pose
    sena["descripcion"] = DESCRIPCION
    partes = datos["version"].split(".")
    partes[-1] = str(int(partes[-1]) + 1)
    datos["version"] = ".".join(partes)
    CATALOGO.write_text(
        json.dumps(datos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Catalogo actualizado (version {datos['version']})")


if __name__ == "__main__":
    guardar(POSE)
