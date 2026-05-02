"""PreviewJPG — encode IMAGE+EXIF as JPEG into ComfyUI's temp folder for the node UI."""
from __future__ import annotations

import random
import string
from pathlib import Path

from ..core.jpeg_writer import tensor_to_pil

try:
    import folder_paths  # type: ignore
except ImportError:
    folder_paths = None


def _temp_dir() -> Path:
    if folder_paths is not None:
        return Path(folder_paths.get_temp_directory())
    return Path("temp")


def _random_suffix(n: int = 5) -> str:
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=n))


class PreviewJPG:
    CATEGORY = "image/exif"
    FUNCTION = "execute"
    RETURN_TYPES = ()
    OUTPUT_NODE = True

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "exif": ("EXIF",),
                "jpg_quality": ("INT", {"default": 92, "min": 1, "max": 100, "step": 1}),
            }
        }

    @classmethod
    def IS_CHANGED(cls, **_kwargs):
        # Force re-execution on every run so the preview reflects the current EXIF.
        return float("nan")

    def execute(self, image, exif, jpg_quality: int):
        if not isinstance(exif, (bytes, bytearray)):
            raise TypeError("exif must be bytes (from EXIFFaker or EXIFCopy).")
        out_dir = _temp_dir()
        out_dir.mkdir(parents=True, exist_ok=True)
        filename = f"exif_preview_{_random_suffix()}.jpg"
        out_path = out_dir / filename

        pil = tensor_to_pil(image)
        save_kwargs = {"format": "JPEG", "quality": int(jpg_quality), "subsampling": 2}
        if exif:
            save_kwargs["exif"] = bytes(exif)
        pil.save(out_path, **save_kwargs)

        return {
            "ui": {
                "images": [
                    {"filename": filename, "subfolder": "", "type": "temp"}
                ]
            }
        }
