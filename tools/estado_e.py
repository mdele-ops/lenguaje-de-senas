"""Comprueba que la E del catalogo y la copia embebida dicen lo mismo."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    cat = json.loads((ROOT / "data" / "catalogo-lsm.json").read_text("utf-8"))
    sena = next(x for x in cat["senas"] if x["letra"] == "E")
    pulgar = {
        k.replace("mixamorig1RightHand", ""): v
        for k, v in sena["pose"]["extra"].items()
        if "Thumb" in k
    }
    print("json  version", cat["version"])
    print("      thumb  ", sena["pose"]["thumb"])
    print("      huesos ", pulgar)

    js = (ROOT / "js" / "catalogo-lsm.js").read_text("utf-8")
    version = re.search(r'"version"\s*:\s*"([^"]+)"', js)
    print("js    version", version.group(1) if version else "?")
    print("      al dia ", version and version.group(1) == cat["version"])


if __name__ == "__main__":
    main()
