"""LoadImageWithEXIF — like the stock LoadImage but also returns raw EXIF bytes."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import piexif
import torch
from PIL import Image, ImageOps

try:
    import folder_paths  # type: ignore
except ImportError:
    folder_paths = None


def _list_input_images() -> list[str]:
    if folder_paths is None:
        return []
    input_dir = Path(folder_paths.get_input_directory())
    if not input_dir.is_dir():
        return []
    return sorted(
        f.name for f in input_dir.iterdir()
        if f.is_file() and f.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp", ".tiff", ".tif"}
    )


class LoadImageWithEXIF:
    CATEGORY = "image/exif"
    FUNCTION = "execute"
    RETURN_TYPES = ("IMAGE", "MASK", "EXIF")
    RETURN_NAMES = ("image", "mask", "exif")

    @classmethod
    def INPUT_TYPES(cls):
        files = _list_input_images() or ["<no images in input dir>"]
        return {
            "required": {
                "image": (files, {"image_upload": True}),
            }
        }

    @classmethod
    def IS_CHANGED(cls, image: str):
        if folder_paths is None:
            return image
        path = Path(folder_paths.get_annotated_filepath(image))
        return str(path.stat().st_mtime) if path.is_file() else image

    def execute(self, image: str):
        if folder_paths is None:
            raise RuntimeError("folder_paths not available; this node requires ComfyUI.")
        path = Path(folder_paths.get_annotated_filepath(image))

        try:
            exif_bytes = piexif.dump(piexif.load(str(path)))
        except Exception:
            exif_bytes = b""

        with Image.open(path) as im:
            im = ImageOps.exif_transpose(im)
            has_alpha = "A" in im.getbands()
            rgb = im.convert("RGB")
            rgb_arr = np.asarray(rgb, dtype=np.float32) / 255.0
            if has_alpha:
                alpha = np.asarray(im.getchannel("A"), dtype=np.float32) / 255.0
                mask_arr = 1.0 - alpha
            else:
                mask_arr = None

        image_tensor = torch.from_numpy(rgb_arr)[None, ...]
        if mask_arr is not None:
            mask_tensor = torch.from_numpy(mask_arr).unsqueeze(0)
        else:
            mask_tensor = torch.zeros((1, 64, 64), dtype=torch.float32)
        return (image_tensor, mask_tensor, exif_bytes)
