"""Cambia el catalogo para que las señas se hagan con una mano u otra.

    py tools/set_rig_side.py left

Reescribe rig.wristBone, rig.huesos y rig.restCorrections. El brazo que no
señala se deja colgando de forma natural.
"""
import sys

import lab

# Postura de reposo hallada con tools/search_rest.py: hombro abajo y adelante,
# codo doblado, antebrazo y dedos hacia arriba, palma hacia el espectador.
SIGNING_ARM = {
    "left": {"arm": [["z", -90], ["x", 120]], "fore": [["x", 150]], "hand": [["y", -15]]},
    "right": {"arm": [["z", 90], ["x", 120]], "fore": [["x", 150]], "hand": [["y", 15]]},
}
# Brazo en descanso: solo baja el hombro, sin doblar el codo.
RESTING_ARM = {"left": [["z", -75], ["x", 90]], "right": [["z", 75], ["x", 90]]}


def main():
    side = sys.argv[1] if len(sys.argv) > 1 else "left"
    other = "right" if side == "left" else "left"
    b = lab.bones(side)
    ob = lab.bones(other)

    catalog = lab.load_catalog()
    rig = catalog["rig"]
    rig["manoQueSenala"] = side
    rig["wristBone"] = b["wrist"]
    rig["huesos"] = {f: list(b[f]) for f in ("thumb", "index", "middle", "ring", "pinky")}

    conf = SIGNING_ARM[side]
    rig["restCorrections"] = [
        {"hueso": b["arm"], "rotaciones": conf["arm"]},
        {"hueso": b["fore"], "rotaciones": conf["fore"]},
        {"hueso": b["wrist"], "rotaciones": conf["hand"]},
        {"hueso": ob["arm"], "rotaciones": RESTING_ARM[other]},
    ]

    lab.save_catalog(catalog)
    print(f"Catalogo configurado para la mano {side}.")


if __name__ == "__main__":
    main()
