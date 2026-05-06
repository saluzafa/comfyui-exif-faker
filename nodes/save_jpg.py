"""SaveJPG — write an IMAGE + EXIF bytes to disk as a JPEG."""
from __future__ import annotations

from pathlib import Path

from ..core import counter
from ..core.filename_tokens import apply_all
from ..core.jpeg_writer import tensor_to_pil

try:
    import folder_paths  # type: ignore
except ImportError:
    folder_paths = None


def _output_dir() -> Path:
    if folder_paths is not None:
        return Path(folder_paths.get_output_directory())
    return Path("output")


class SaveJPG:
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
                "filename_prefix": ("STRING", {"default": "IMG"}),
            }
        }

    def execute(self, image, exif, jpg_quality: int, filename_prefix: str):
        if not isinstance(exif, (bytes, bytearray)):
            raise TypeError("exif must be bytes (from EXIFFaker or EXIFCopy).")
        prefix = filename_prefix or "IMG"
        pil = tensor_to_pil(image)
        prefix = apply_all(prefix, pil.width, pil.height)

        if folder_paths is not None:
            full_output_folder, filename, _, subfolder, _ = folder_paths.get_save_image_path(
                prefix, folder_paths.get_output_directory(), pil.width, pil.height
            )
            out_dir = Path(full_output_folder)
            out_path = counter.next_path(out_dir, prefix=filename)
        else:
            out_dir = _output_dir()
            out_path = counter.next_path(out_dir, prefix=prefix)
            try:
                rel = out_path.parent.relative_to(out_dir)
                subfolder = "" if str(rel) == "." else str(rel)
            except ValueError:
                subfolder = ""

        save_kwargs = {"format": "JPEG", "quality": int(jpg_quality), "subsampling": 2}
        if exif:
            save_kwargs["exif"] = bytes(exif)
        pil.save(out_path, **save_kwargs)

        return {
            "ui": {
                "images": [
                    {"filename": out_path.name, "subfolder": subfolder, "type": "output"}
                ]
            }
        }
