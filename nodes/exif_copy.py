"""EXIFCopy — pass IMAGE through with EXIF rewritten to match its dimensions."""
from __future__ import annotations

import piexif


def _tensor_hw(image) -> tuple[int, int]:
    shape = image.shape if hasattr(image, "shape") else (1, 0, 0, 3)
    return int(shape[1]), int(shape[2])


def _rebuild_with_target_size(exif_bytes: bytes, width: int, height: int) -> bytes:
    """Rewrite ImageWidth/Length and PixelXDimension/PixelYDimension; drop thumbnail."""
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
    d["1st"] = {}
    d["thumbnail"] = None
    try:
        return piexif.dump(d)
    except Exception:
        return exif_bytes


class EXIFCopy:
    CATEGORY = "image/exif"
    FUNCTION = "execute"
    RETURN_TYPES = ("IMAGE", "EXIF")
    RETURN_NAMES = ("image", "exif")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "target_image": ("IMAGE",),
                "exif_source": ("EXIF",),
            }
        }

    def execute(self, target_image, exif_source):
        if not isinstance(exif_source, (bytes, bytearray)):
            raise TypeError("exif_source must be bytes (from LoadImageWithEXIF).")
        height, width = _tensor_hw(target_image)
        exif_bytes = _rebuild_with_target_size(bytes(exif_source), width, height)
        return (target_image, exif_bytes)
