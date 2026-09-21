"""Construye una mascara precisa (rasterizando triangulos UV reales) para la
cabeza/rostro del personaje, usando los pesos de skinning del hueso Head."""
import struct
from pathlib import Path

import cv2
import numpy as np
from pygltflib import GLTF2
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "model.original.glb"
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


skin = gltf.skins[0]
joint_node_indices = skin.joints
joint_names = [gltf.nodes[j].name for j in joint_node_indices]
head_keywords = ["Head"]
head_joint_local_idx = set(i for i, nm in enumerate(joint_names) if nm and any(k in nm for k in head_keywords))

mesh = gltf.meshes[0]
prim = mesh.primitives[0]
joints0 = accessor_data(prim.attributes.JOINTS_0).astype(int)
weights0 = accessor_data(prim.attributes.WEIGHTS_0)
uv = accessor_data(prim.attributes.TEXCOORD_0)
indices = accessor_data(prim.indices).astype(int).reshape(-1)

vert_mask = np.zeros(len(joints0), dtype=bool)
for row in range(len(joints0)):
    for c in range(4):
        j = joints0[row, c]
        w = weights0[row, c]
        if w > 0.1 and j in head_joint_local_idx:
            vert_mask[row] = True
            break

print("Vertices marcados:", vert_mask.sum(), "/", len(vert_mask))

tris = indices.reshape(-1, 3)
tri_mask = vert_mask[tris].any(axis=1)
selected_tris = tris[tri_mask]
print("Triangulos seleccionados:", len(selected_tris), "/", len(tris))

SIZE = 4096
canvas = np.zeros((SIZE, SIZE), dtype=np.uint8)
uv_px = np.empty_like(uv)
uv_px[:, 0] = uv[:, 0] * SIZE
uv_px[:, 1] = uv[:, 1] * SIZE

for tri in selected_tris:
    pts = uv_px[tri].astype(np.int32).reshape(1, 3, 2)
    cv2.fillPoly(canvas, pts, 255)

canvas = cv2.dilate(canvas, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))

out_path = ROOT / "tools" / "garment_masks" / "mask_head.png"
Image.fromarray(canvas).save(str(out_path))
ys, xs = np.where(canvas > 0)
print("Mascara guardada en", out_path, "cobertura px:", int((canvas > 0).sum()),
      "bbox x", xs.min(), xs.max(), "y", ys.min(), ys.max())
