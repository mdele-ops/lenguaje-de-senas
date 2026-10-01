"""Etapa 1 de la C: encontrar el giro de muneca que deja el arco de frente."""
import c_lab
import lab

CASES = {"actual": next(
    s for s in lab.load_catalog()["senas"] if s["letra"] == "C"
)["pose"]}

for wy in (50, 70, 90, 110):
    for wz in (-20, 0, 25, 45):
        CASES[f"wy{wy}_wz{wz:+d}"] = c_lab.build(wy=wy, wz=wz)


if __name__ == "__main__":
    c_lab.run("c_stage1", CASES, orbits=(0,), cols=6, cell=250)
