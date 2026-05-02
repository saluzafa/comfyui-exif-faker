"""ComfyUI EXIF Faker — fake or copy EXIF metadata on generated images."""
from .nodes.exif_copy import EXIFCopy
from .nodes.exif_faker import EXIFFaker
from .nodes.load_image_with_exif import LoadImageWithEXIF

NODE_CLASS_MAPPINGS = {
    "EXIFFaker": EXIFFaker,
    "LoadImageWithEXIF": LoadImageWithEXIF,
    "EXIFCopy": EXIFCopy,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "EXIFFaker": "EXIF Faker (fake camera metadata)",
    "LoadImageWithEXIF": "Load Image (with EXIF)",
    "EXIFCopy": "EXIF Copy (transfer metadata)",
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
