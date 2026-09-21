"""Limpia manchas/suciedad de TODA la textura del personaje (piel de mano y
antebrazo + ropa: chaleco, camisa, pantalon, botas) y reincrusta la textura
corregida en una copia nueva del GLB. Parte siempre de model.original.glb
para que sea repetible.
"""
import io
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from pygltflib import BufferView, GLTF2
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
BACKUP_GLB = ROOT / "model.original.glb"
OUT_GLB = ROOT / "model.glb"
TOOLS = ROOT / "tools"
GARMENT_DIR = TOOLS / "garment_masks"

SIZE = 4096


def load_mask(path):
    arr = np.array(Image.open(str(path)).convert("L"))
    return (arr > 0).astype(np.uint8)


def feather(mask_bool, close_iter=6, blur_sigma=8):
    m = ndimage.binary_closing(mask_bool, iterations=close_iter).astype(np.uint8)
    a = ndimage.gaussian_filter(m.astype(np.float32), sigma=blur_sigma)
    return np.clip(a, 0.0, 1.0)


def clean_uniform_garment(img, mask_bool, reference_color, close_kernel=181,
                           blur_sigma=30, shade_clip=(0.85, 1.15), strength=0.85,
                           fine_weight=0.15):
    """Para prendas de un solo tono (camisa, pantalon): reconstruye un color
    de tela limpio (parecido a la piel: tono de referencia * sombreado
    normalizado), conservando un poco de detalle fino para que no se vea
    plano."""
    luma = img.mean(axis=2)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (close_kernel, close_kernel))
    closed = cv2.morphologyEx(luma, cv2.MORPH_CLOSE, kernel)
    closed = cv2.GaussianBlur(closed, (0, 0), sigmaX=blur_sigma, sigmaY=blur_sigma)
    mean_in_mask = closed[mask_bool].mean()
    shade = np.clip(closed / mean_in_mask, shade_clip[0], shade_clip[1])

    clean = reference_color[None, None, :] * shade[..., None]
    fine_detail = img - cv2.GaussianBlur(img, (0, 0), sigmaX=6, sigmaY=6)
    clean = np.clip(clean + fine_detail * fine_weight, 0, 255)

    alpha = feather(mask_bool) * strength
    alpha3 = alpha[..., None]
    return img * (1 - alpha3) + clean * alpha3


def recolor_hue(img, mask_bool, hue_center, hue_span, target_hue_deg,
                 sat_min=40, sat_boost=1.0, val_scale=1.0):
    """Cambia el tono (H) de los pixeles de la prenda cuyo color caiga cerca
    de `hue_center` (grados/2, escala OpenCV 0-179), conservando su
    saturacion/valor (sombras, pliegues, brillos) para no perder el volumen
    de la tela. Se usa un borde suave (smoothstep) para que la transicion
    hacia colores que no se tocan (p. ej. las franjas reflectantes) sea
    gradual y no deje un corte duro."""
    hsv = cv2.cvtColor(np.clip(img, 0, 255).astype(np.uint8), cv2.COLOR_RGB2HSV).astype(np.float32)
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]

    hue_dist = np.abs(h - hue_center)
    hue_dist = np.minimum(hue_dist, 180 - hue_dist)
    hue_w = np.clip(1.0 - (hue_dist - hue_span * 0.5) / (hue_span * 0.5), 0.0, 1.0)
    sat_w = np.clip((s - sat_min) / 25.0, 0.0, 1.0)
    alpha = hue_w * sat_w * mask_bool.astype(np.float32)

    target_h = (target_hue_deg / 2.0) % 180
    new_h = (h * (1 - alpha) + target_h * alpha)
    new_s = np.clip(s * (1 + (sat_boost - 1) * alpha), 0, 255)
    new_v = np.clip(v * (1 + (val_scale - 1) * alpha), 0, 255)

    new_hsv = np.stack([new_h, new_s, new_v], axis=-1).astype(np.uint8)
    out = cv2.cvtColor(new_hsv, cv2.COLOR_HSV2RGB).astype(np.float32)
    return out


def warm_glow(img, mask_bool, warm_rgb=(1.04, 1.015, 0.99), brightness=1.03,
              sat_boost=1.08, strength=1.0):
    """Ajuste de color suave (no destructivo) para dar un aspecto mas
    saludable/alegre: un poco mas de calidez, brillo y viveza, sin tocar
    ningun rasgo (ojos, cejas, orejas, etc.)."""
    warmed = img * np.array(warm_rgb, dtype=np.float32)[None, None, :] * brightness
    warmed = np.clip(warmed, 0, 255)

    hsv = cv2.cvtColor(warmed.astype(np.uint8), cv2.COLOR_RGB2HSV).astype(np.float32)
    hsv[..., 1] = np.clip(hsv[..., 1] * sat_boost, 0, 255)
    warmed = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB).astype(np.float32)

    alpha = feather(mask_bool, close_iter=3, blur_sigma=6) * strength
    alpha3 = alpha[..., None]
    return img * (1 - alpha3) + warmed * alpha3


def degrunge(img, mask_bool, close_kernel, blur_sigma, max_boost=1.6, strength=1.0):
    """Aclara manchas oscuras (suciedad) preservando el tono/color propio de
    cada pixel: normaliza la luminancia local respecto a un cierre
    morfologico (elimina manchas mas chicas que el kernel) y reescala cada
    canal por igual para no perder el color/patron original (rayas, costuras,
    dibujo de suela, etc.)."""
    luma = img.mean(axis=2)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (close_kernel, close_kernel))
    closed = cv2.morphologyEx(luma, cv2.MORPH_CLOSE, kernel)
    closed = cv2.GaussianBlur(closed, (0, 0), sigmaX=blur_sigma, sigmaY=blur_sigma)
    ratio = closed / np.maximum(luma, 3.0)
    ratio = np.clip(ratio, 1.0, max_boost)
    cleaned = img * ratio[..., None]
    cleaned = np.clip(cleaned, 0, 255)

    alpha = feather(mask_bool) * strength
    alpha3 = alpha[..., None]
    return img * (1 - alpha3) + cleaned * alpha3


# ---------------------------------------------------------------------------
# Cargar textura original directamente del GLB original (sin depender de un
# archivo PNG extra ya guardado en disco).
# ---------------------------------------------------------------------------
_src_gltf = GLTF2().load(str(BACKUP_GLB))
_src_blob = _src_gltf.binary_blob()
_src_img = _src_gltf.images[0]
_src_bv = _src_gltf.bufferViews[_src_img.bufferView]
_base_bytes = _src_blob[_src_bv.byteOffset: _src_bv.byteOffset + _src_bv.byteLength]
img = np.array(Image.open(io.BytesIO(_base_bytes)).convert("RGB")).astype(np.float32)
original_png_size = len(_base_bytes)

# ---------------------------------------------------------------------------
# 1. Piel de mano + antebrazo (igual que antes: tono de referencia limpio).
# ---------------------------------------------------------------------------
hand_mask = load_mask(TOOLS / "hand_mask_precise.png").astype(bool)
hand_mask_closed = ndimage.binary_closing(hand_mask, iterations=6).astype(np.uint8)
hand_alpha = np.clip(ndimage.gaussian_filter(hand_mask_closed.astype(np.float32), sigma=8), 0, 1)

luma = img.mean(axis=2)
kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (181, 181))
luma_closed = cv2.morphologyEx(luma, cv2.MORPH_CLOSE, kernel)
luma_blur = cv2.GaussianBlur(luma_closed, (0, 0), sigmaX=30, sigmaY=30)

reference_color = np.array([183.5, 147.0, 132.5], dtype=np.float32)
luma_mean_in_mask = luma_blur[hand_mask].mean()
shade_factor = np.clip(luma_blur / luma_mean_in_mask, 0.94, 1.09)
clean_hand = reference_color[None, None, :] * shade_factor[..., None]
fine_detail = img - cv2.GaussianBlur(img, (0, 0), sigmaX=6, sigmaY=6)
clean_hand = np.clip(clean_hand + fine_detail * 0.05, 0, 255)

alpha3 = hand_alpha[..., None]
img = img * (1 - alpha3) + clean_hand * alpha3

# ---------------------------------------------------------------------------
# 2. Ropa: chaleco, camisa, pantalon y botas. Se preserva el color/patron de
#    cada prenda (rayas reflectantes, costuras, dibujo de suela) y solo se
#    aclaran las manchas oscuras de suciedad.
# ---------------------------------------------------------------------------
# Chaleco y botas: multiples tonos/patrones (rayas, cuero veteado, suela) ->
# solo se aclaran las manchas oscuras conservando el color/patron propio.
degrunge_params = {
    # (kernel de cierre, sigma de difuminado, boost maximo, intensidad)
    "vest": (71, 20, 1.35, 1.0),
    "boots": (51, 14, 1.35, 0.7),
}
for name, (k, s, boost, strength) in degrunge_params.items():
    mask = load_mask(GARMENT_DIR / f"mask_{name}.png").astype(bool)
    img = degrunge(img, mask, close_kernel=k, blur_sigma=s, max_boost=boost, strength=strength)

# Camisa y pantalon: tela de un solo tono, muy sucia de forma pareja -> se
# reconstruye con un tono de tela limpio (igual criterio que la piel).
uniform_garment_params = {
    # (color de referencia limpio RGB, strength)
    "shirt": (np.array([108.0, 100.0, 98.0], dtype=np.float32), 0.85),
    "pants": (np.array([138.0, 118.0, 92.0], dtype=np.float32), 0.85),
}
for name, (ref_color, strength) in uniform_garment_params.items():
    mask = load_mask(GARMENT_DIR / f"mask_{name}.png").astype(bool)
    img = clean_uniform_garment(img, mask, ref_color, strength=strength)

# ---------------------------------------------------------------------------
# 3. Recolorar el chaleco de naranja a azul (se conservan las franjas
#    reflectantes amarillas y las sombras/pliegues del propio tono naranja
#    original, solo se cambia el matiz).
# ---------------------------------------------------------------------------
vest_mask = load_mask(GARMENT_DIR / "mask_vest.png").astype(bool)
img = recolor_hue(
    img, vest_mask,
    hue_center=8, hue_span=22, target_hue_deg=215,
    sat_min=35, sat_boost=1.45, val_scale=0.92,
)

# ---------------------------------------------------------------------------
# 3b. Rostro: un toque de calidez/brillo/viveza para que se vea mas alegre y
#     amigable, sin alterar ningun rasgo facial (ojos, cejas, orejas, etc.).
# ---------------------------------------------------------------------------
head_mask_path = GARMENT_DIR / "mask_head.png"
if head_mask_path.exists():
    head_mask = load_mask(head_mask_path).astype(bool)
    img = warm_glow(img, head_mask, strength=0.9)

result = np.clip(img, 0, 255).astype(np.uint8)
out_img = Image.fromarray(result, mode="RGB")
clean_png_path = TOOLS / "base_color_clean_full.png"
out_img.save(str(clean_png_path), optimize=True)
print("Textura completa limpia guardada en", clean_png_path)

# ---------------------------------------------------------------------------
# 4. Reincrustar en una copia nueva del GLB (siempre partiendo del original).
# ---------------------------------------------------------------------------
buf = io.BytesIO()
out_img.save(buf, format="PNG", optimize=True)
new_bytes = buf.getvalue()
print("Nuevo PNG:", len(new_bytes), "bytes (original", original_png_size, ")")

gltf = GLTF2().load(str(BACKUP_GLB))
image = gltf.images[0]
old_bv_index = image.bufferView
bv = gltf.bufferViews[old_bv_index]

gltf.remove_data_from_buffer(bv.byteOffset, bv.byteLength)
gltf.remove_bufferView(old_bv_index)

blob = gltf.binary_blob()
new_offset = len(blob)
blob = blob + new_bytes
pad = (-len(new_bytes)) % 4
if pad:
    blob = blob + b"\x00" * pad

gltf.set_binary_blob(blob)
gltf.buffers[0].byteLength = len(blob)

new_bv = BufferView(buffer=0, byteOffset=new_offset, byteLength=len(new_bytes))
gltf.bufferViews.append(new_bv)
image.bufferView = len(gltf.bufferViews) - 1
image.uri = None
image.mimeType = "image/png"

gltf.save(str(OUT_GLB))
print("GLB limpio guardado en", OUT_GLB)
