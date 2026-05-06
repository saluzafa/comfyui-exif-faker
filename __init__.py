"""ComfyUI EXIF Faker — fake or copy EXIF metadata on generated images."""
from .nodes.exif_copy import EXIFCopy
from .nodes.exif_faker import EXIFFaker
from .nodes.load_image_with_exif import LoadImageWithEXIF
from .nodes.preview_jpg import PreviewJPG
from .nodes.save_jpg import SaveJPG
from .nodes.save_video import SaveVideoWithEXIF

NODE_CLASS_MAPPINGS = {
    "EXIFFaker": EXIFFaker,
    "EXIFCopy": EXIFCopy,
    "LoadImageWithEXIF": LoadImageWithEXIF,
    "SaveJPG": SaveJPG,
    "PreviewJPG": PreviewJPG,
    "SaveVideoWithEXIF": SaveVideoWithEXIF,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "EXIFFaker": "EXIF Faker (fake camera metadata)",
    "EXIFCopy": "EXIF Copy (transfer metadata)",
    "LoadImageWithEXIF": "Load Image (with EXIF)",
    "SaveJPG": "Save JPG (with EXIF)",
    "PreviewJPG": "Preview JPG (with EXIF)",
    "SaveVideoWithEXIF": "Save Video (with EXIF)",
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
