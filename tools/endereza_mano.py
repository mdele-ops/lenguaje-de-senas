"""Compensa el giro de reposo del antebrazo en las letras ya orientadas a mano.

El reposo del rig giraba la mano ~25 grados a la izquierda, asi que TODAS las
letras salian inclinadas. Al enderezar rig.restCorrections (RightForeArm y:
-77 -> -102.2) las letras verticales quedan a 90 grados, pero las que ya se
habian orientado a mano (C, G, H, M, N, N-tilde, O, P, Q, X, Y) se pasaban de
vuelta. Este script les devuelve su orientacion previa con un giro inverso del
antebrazo, y deja la A vertical como el resto del grupo.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOGO = ROOT / "data" / "catalogo-lsm.json"

# Grados de giro del antebrazo (eje y) que cada letra necesita para conservar
# la orientacion con la que fue calibrada. 25.2 cancela exactamente la
# correccion de reposo; A e Y se resolvieron numericamente sobre el modelo.
COMPENSACION = {
    "A": 5.5,
    "C": 25.2,
    "G": 25.2,
    "H": 25.2,
    "M": 25.2,
    "N": 25.2,
    "Ñ": 25.2,
    "O": 25.2,
    "P": 25.2,
    "Q": 25.2,
    "X": 25.2,
    "Y": 24.1,
}


def main():
    data = json.loads(CATALOGO.read_text(encoding="utf-8"))
    for sena in data["senas"]:
        grados = COMPENSACION.get(sena["letra"])
        if grados is None or not sena.get("pose"):
            continue
        extra = sena["pose"].setdefault("extra", {})
        antebrazo = extra.setdefault("RightForeArm", {})
        antebrazo["y"] = grados
        print(f"{sena['letra']}: RightForeArm.y = {grados}")
    CATALOGO.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"OK: {CATALOGO.name} actualizado")


if __name__ == "__main__":
    main()
