"""Escribe en el catalogo la O redonda elegida en o_redonda.py."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOGO = ROOT / "data" / "catalogo-lsm.json"
ELEGIDA = ROOT / "tools" / "screenshots" / "o_redonda" / "cmp.json"

DESCRIPCION = (
    "Mano de perfil delante del pecho, palma hacia el costado: los cuatro dedos, "
    "juntos y curvados por igual, bajan formando el arco de arriba y el pulgar sube "
    "a su encuentro hasta que las yemas se tocan, dejando un hueco redondo con la "
    "forma de la letra O."
)


def main():
    cat = json.loads(CATALOGO.read_text(encoding="utf-8"))
    pose = json.loads(ELEGIDA.read_text(encoding="utf-8"))["3_nueva"]
    sena = next(s for s in cat["senas"] if s["letra"] == "O")
    sena["pose"] = pose
    sena["descripcion"] = DESCRIPCION
    cat["version"] = "1.4.5"
    CATALOGO.write_text(
        json.dumps(cat, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(pose))


if __name__ == "__main__":
    main()
