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
    RETURN_TYPES = ("IMAGE", "EXIF")
    RETURN_NAMES = ("image", "exif")

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
            im = im.convert("RGB")
            arr = np.asarray(im, dtype=np.float32) / 255.0
        tensor = torch.from_numpy(arr)[None, ...]
        return (tensor, exif_bytes)
