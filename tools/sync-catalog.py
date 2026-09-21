"""Sincroniza data/catalogo-lsm.json -> js/catalogo-lsm.js (catálogo embebido)."""
from pathlib import Path
import json

root = Path(__file__).resolve().parents[1]
src = root / "data" / "catalogo-lsm.json"
dst = root / "js" / "catalogo-lsm.js"

data = json.loads(src.read_text(encoding="utf-8"))
dst.write_text(
    "/* Generado desde data/catalogo-lsm.json — no editar a mano */\n"
    "window.LSM_CATALOG = "
    + json.dumps(data, ensure_ascii=False, indent=2)
    + ";\n",
    encoding="utf-8",
)
print(f"OK: {src.name} -> {dst.relative_to(root)}")
