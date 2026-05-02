"""Load and patch an Apple MakerNote template blob.

The Apple MakerNote is a proprietary TIFF-IFD-shaped binary structure. Decoding it
fully would require porting ExifTool's Apple.pm tag table. For v1 we treat the blob as
opaque bytes captured from a real device and pass it through as-is. Dynamic per-shot
patching (acceleration vector, ContentIdentifier UUID, ImageUniqueID) is a TODO that
would require a minimal Apple-IFD parser; for now we log a notice and ship the static
template, which is still vastly more authentic than no MakerNote.

To install a template: extract one from any real iPhone 15 Pro JPG with
    exiftool -MakerNote -b photo.jpg > profiles/iphone_15_pro.makernote.bin
"""
from __future__ import annotations

import logging
from pathlib import Path

log = logging.getLogger(__name__)

_warned_missing: set[str] = set()
_warned_dynamic: set[str] = set()


def load(path: Path | None, dynamic_fields: list[str] | None = None) -> bytes | None:
    """Return MakerNote bytes for embedding, or None if unavailable."""
    if path is None:
        return None
    if not path.is_file():
        key = str(path)
        if key not in _warned_missing:
            log.warning(
                "MakerNote template not found at %s — saving without MakerNote. "
                "See core/makernote.py docstring for how to capture one.",
                path,
            )
            _warned_missing.add(key)
        return None
    blob = path.read_bytes()
    if dynamic_fields:
        key = str(path)
        if key not in _warned_dynamic:
            log.info(
                "MakerNote dynamic patching (%s) is not yet implemented; "
                "shipping static template bytes from %s.",
                ",".join(dynamic_fields),
                path.name,
            )
            _warned_dynamic.add(key)
    return blob
