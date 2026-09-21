"""Arma la lamina antes / despues / referencia de la letra C."""
from pathlib import Path

import lab

ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / "tools" / "screenshots"
OUT = SHOTS / "c_antes_despues"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    lab.sheet(
        [
            ("ANTES (pinza)", SHOTS / "c_final" / "cerca_F_actual_en_disco.png"),
            ("DESPUES (arco de C)", SHOTS / "verify_c" / "primer_plano.png"),
            ("FOTO DE REFERENCIA", SHOTS / "ref_c" / "ref_c_original.png"),
        ],
        OUT / "c_antes_despues.png",
        cols=3,
        cell=380,
    )


if __name__ == "__main__":
    main()
