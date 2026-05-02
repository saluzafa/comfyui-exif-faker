"""Discover and load device profiles from the profiles/ folder."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

PROFILES_DIR = Path(__file__).resolve().parent.parent / "profiles"


@dataclass(frozen=True)
class Profile:
    display_name: str
    make: str
    model: str
    software: str
    lens_make: str
    lens_model: str
    focal_length_mm: float
    focal_length_35mm: int
    aperture: float
    defaults: dict[str, Any]
    exif_extras: dict[str, Any]
    makernote: dict[str, Any]
    source_path: Path

    @property
    def makernote_path(self) -> Path | None:
        template = self.makernote.get("template_file") if self.makernote else None
        if not template:
            return None
        return self.source_path.parent / template


_REQUIRED_FIELDS = (
    "display_name", "make", "model", "software", "lens_make", "lens_model",
    "focal_length_mm", "focal_length_35mm", "aperture", "defaults", "exif_extras",
)


def _load_one(path: Path) -> Profile | None:
    try:
        data = json.loads(path.read_text())
    except Exception as e:
        log.warning("Failed to parse profile %s: %s", path, e)
        return None
    missing = [f for f in _REQUIRED_FIELDS if f not in data]
    if missing:
        log.warning("Profile %s missing required fields: %s", path, missing)
        return None
    return Profile(
        display_name=data["display_name"],
        make=data["make"],
        model=data["model"],
        software=data["software"],
        lens_make=data["lens_make"],
        lens_model=data["lens_model"],
        focal_length_mm=float(data["focal_length_mm"]),
        focal_length_35mm=int(data["focal_length_35mm"]),
        aperture=float(data["aperture"]),
        defaults=dict(data["defaults"]),
        exif_extras=dict(data["exif_extras"]),
        makernote=dict(data.get("makernote") or {}),
        source_path=path,
    )


def discover() -> dict[str, Profile]:
    """Return {display_name: Profile} for every valid JSON in profiles/."""
    out: dict[str, Profile] = {}
    if not PROFILES_DIR.is_dir():
        return out
    for path in sorted(PROFILES_DIR.glob("*.json")):
        prof = _load_one(path)
        if prof is not None:
            out[prof.display_name] = prof
    return out
