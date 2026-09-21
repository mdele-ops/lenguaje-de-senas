"""Construye mascaras precisas (rasterizando triangulos UV reales) para cada
prenda del personaje: botas, casco, chaleco, camisa y pantalon."""
import struct
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from pygltflib import GLTF2

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "model.original.glb"
if not SRC.exists():
    SRC = ROOT / "model2.glb"
gltf = GLTF2().load(str(SRC))
blob = gltf.binary_blob()

COMP_TYPES = {5120: ("b", 1), 5121: ("B", 1), 5122: ("h", 2), 5123: ("H", 2), 5125: ("I", 4), 5126: ("f", 4)}
TYPE_COUNTS = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}


def accessor_data(idx):
    acc = gltf.accessors[idx]
    bv = gltf.bufferViews[acc.bufferView]
    fmt_char, comp_size = COMP_TYPES[acc.componentType]
    n_comp = TYPE_COUNTS[acc.type]
    stride = bv.byteStride or (comp_size * n_comp)
    start = (bv.byteOffset or 0) + (acc.byteOffset or 0)
    out = np.zeros((acc.count, n_comp), dtype=np.float64)
    for i in range(acc.count):
        offset = start + i * stride
        vals = struct.unpack_from("<" + fmt_char * n_comp, blob, offset)
        out[i] = vals
    if acc.normalized and acc.componentType == 5121:
        out = out / 255.0
    return out


SIZE = 4096
OUT_DIR = ROOT / "tools" / "garment_masks"
OUT_DIR.mkdir(exist_ok=True)

garments = {
    "boots": 1,
    "helmet": 2,
    "vest": 3,
    "shirt": 4,
    "pants": 5,
}

for name, mesh_idx in garments.items():
    mesh = gltf.meshes[mesh_idx]
    prim = mesh.primitives[0]
    uv = accessor_data(prim.attributes.TEXCOORD_0)
    indices = accessor_data(prim.indices).astype(int).reshape(-1)
    tris = indices.reshape(-1, 3)

    uv_px = np.empty_like(uv)
    uv_px[:, 0] = uv[:, 0] * SIZE
    uv_px[:, 1] = uv[:, 1] * SIZE

    canvas = np.zeros((SIZE, SIZE), dtype=np.uint8)
    for tri in tris:
        pts = uv_px[tri].astype(np.int32).reshape(1, 3, 2)
        cv2.fillPoly(canvas, pts, 255)
    canvas = cv2.dilate(canvas, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))

    Image.fromarray(canvas).save(str(OUT_DIR / f"mask_{name}.png"))
    ys, xs = np.where(canvas > 0)
    if len(xs):
        print(name, "mesh", mesh.name, "cobertura px:", int((canvas > 0).sum()),
              "bbox x", xs.min(), xs.max(), "y", ys.min(), ys.max())
    else:
        print(name, "sin cobertura!")
