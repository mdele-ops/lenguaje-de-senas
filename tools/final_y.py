"""Y final: pulgar arriba y meñique a un lado, como la lámina.

La Y del catálogo era una I con el pulgar abierto (meñique hacia arriba,
sin muñeca). En la foto el pulgar es el palito de arriba y el meñique el
de la derecha, ~90°. La J enseña el eje: muneca.z positivo manda el
meñique a la izquierda del espectador y deja el pulgar arriba (el gancho
de la J). Se usa un giro menor que ese gancho para no tumbar el antebrazo
sobre el pecho, y el brazo acompaña para que la muñeca no se quiebre.
"""
from pathlib import Path
import json

from pose_lab_y import pose_y

ROOT = Path(__file__).resolve().parents[1]
CATALOGO = ROOT / "data" / "catalogo-lsm.json"

POSE = pose_y(
    wx=6,
    wz=52,
    p_spread=22,
    tcurl=0.0,
    taside=0.85,
    fist=0.98,
    t1={"z": 16},
    fx=8,
    fz=6,
    arm_z=-18,
)

DESCRIPCION = (
    "Pulgar estirado hacia arriba y meñique hacia un lado, formando la Y; "
    "índice, medio y anular se cierran contra la palma. La muñeca gira en "
    "el plano de la palma para que se lean los dos palitos, con el antebrazo "
    "en diagonal y la muñeca alineada (sin quebrarla)."
)


def guardar(pose):
    datos = json.loads(CATALOGO.read_text(encoding="utf-8"))
    sena = next(s for s in datos["senas"] if s["letra"] == "Y")
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
