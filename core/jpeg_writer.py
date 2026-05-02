"""Convert a ComfyUI IMAGE tensor to a JPEG file with embedded EXIF."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import piexif
from PIL import Image


def tensor_to_pil(image_tensor: Any) -> Image.Image:
    """ComfyUI IMAGE tensors are torch tensors of shape [B, H, W, C], float 0-1.

    We take the first image in the batch and convert to an 8-bit RGB PIL image.
    """
    arr = image_tensor
    if hasattr(arr, "detach"):
        arr = arr.detach().cpu().numpy()
    arr = np.asarray(arr)
    if arr.ndim == 4:
        arr = arr[0]
    if arr.dtype != np.uint8:
        arr = np.clip(arr * 255.0 + 0.5, 0, 255).astype(np.uint8)
    if arr.ndim == 2:
        return Image.fromarray(arr, mode="L").convert("RGB")
    if arr.shape[2] == 4:
        arr = arr[:, :, :3]
    return Image.fromarray(arr, mode="RGB")


def save(
    image_tensor: Any,
    out_path: Path,
    *,
    quality: int,
    exif_bytes: bytes | None,
) -> tuple[int, int]:
    """Save the tensor as JPEG. Returns (width, height) of the written image."""
    pil = tensor_to_pil(image_tensor)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    save_kwargs: dict[str, Any] = {
        "format": "JPEG",
        "quality": int(quality),
        "subsampling": 2,
    }
    if exif_bytes:
        save_kwargs["exif"] = exif_bytes
    pil.save(out_path, **save_kwargs)
    return pil.width, pil.height


def dump_exif_for_size(exif_dict: dict, width: int, height: int) -> bytes:
    """Patch PixelXDimension/PixelYDimension and dump to bytes."""
    exif_dict.setdefault("Exif", {})
    exif_dict["Exif"][piexif.ExifIFD.PixelXDimension] = int(width)
    exif_dict["Exif"][piexif.ExifIFD.PixelYDimension] = int(height)
    return piexif.dump(exif_dict)
