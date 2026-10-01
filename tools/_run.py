"""Lanzador para el python embebido: `python _run.py mira_e2.py [args]`.

El interprete embebido lleva un `python312._pth`, y con el no se anade la
carpeta del script a `sys.path` ni se lee `PYTHONPATH`. Sin esto cualquier
script de tools/ falla al importar a sus vecinos (compare_e10, pose_lab_e...).
"""
import runpy
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    if len(sys.argv) < 2:
        raise SystemExit("uso: python _run.py <script.py> [args]")
    destino = HERE / sys.argv[1]
    sys.path.insert(0, str(HERE))
    sys.argv = [str(destino)] + sys.argv[2:]
    runpy.run_path(str(destino), run_name="__main__")


if __name__ == "__main__":
    main()
