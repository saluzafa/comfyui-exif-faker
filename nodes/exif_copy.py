"""EXIFCopy — save target IMAGE as JPG with EXIF copied verbatim from another source."""
from __future__ import annotations

from pathlib import Path

import piexif

from ..core import counter
from ..core.jpeg_writer import tensor_to_pil

try:
    import folder_paths  # type: ignore
except ImportError:
    folder_paths = None


def _output_dir() -> Path:
    if folder_paths is not None:
        return Path(folder_paths.get_output_directory())
    return Path("output")


def _rebuild_with_target_size(exif_bytes: bytes, width: int, height: int) -> bytes:
    """Rewrite PixelXDimension/PixelYDimension and ImageWidth/Length to match the
    saved target image; otherwise viewers will misreport dimensions."""
    try:
        d = piexif.load(exif_bytes)
    except Exception:
        return exif_bytes
    d.setdefault("0th", {})
    d.setdefault("Exif", {})
    d["0th"][piexif.ImageIFD.ImageWidth] = int(width)
    d["0th"][piexif.ImageIFD.ImageLength] = int(height)
    d["Exif"][piexif.ExifIFD.PixelXDimension] = int(width)
    d["Exif"][piexif.ExifIFD.PixelYDimension] = int(height)
    # Strip any embedded thumbnail — it would be at the wrong size.
    d["1st"] = {}
    d["thumbnail"] = None
    try:
        return piexif.dump(d)
    except Exception:
        return exif_bytes


class EXIFCopy:
    CATEGORY = "image/exif"
    FUNCTION = "execute"
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    OUTPUT_NODE = True

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "target_image": ("IMAGE",),
                "exif_source": ("EXIF",),
                "jpg_quality": ("INT", {"default": 92, "min": 1, "max": 100, "step": 1}),
                "filename_prefix": ("STRING", {"default": "IMG"}),
            }
        }

    def execute(self, target_image, exif_source, jpg_quality: int, filename_prefix: str):
        if not isinstance(exif_source, (bytes, bytearray)):
            raise TypeError("exif_source must be bytes (from LoadImageWithEXIF).")
        pil = tensor_to_pil(target_image)
        exif_bytes = _rebuild_with_target_size(bytes(exif_source), pil.width, pil.height)

        out_path = counter.next_path(_output_dir(), prefix=filename_prefix or "IMG")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        save_kwargs = {"format": "JPEG", "quality": int(jpg_quality), "subsampling": 2}
        if exif_bytes:
            save_kwargs["exif"] = exif_bytes
        pil.save(out_path, **save_kwargs)
        return (target_image,)
