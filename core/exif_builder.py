"""Build a piexif EXIF dict from a Profile + per-shot user inputs."""
from __future__ import annotations

import datetime as _dt
from fractions import Fraction
from typing import Any

import piexif

from .profiles import Profile


def _to_rational(value: float, max_denom: int = 1_000_000) -> tuple[int, int]:
    f = Fraction(value).limit_denominator(max_denom)
    return f.numerator, f.denominator


def _parse_shutter(s: str) -> tuple[int, int]:
    """Accept '1/120', '0.5', '2', etc. → (num, denom)."""
    s = s.strip()
    if "/" in s:
        num_s, den_s = s.split("/", 1)
        return int(float(num_s)), int(float(den_s))
    return _to_rational(float(s))


def _parse_dt(s: str) -> _dt.datetime:
    """Accept 'YYYY:MM:DD HH:MM:SS' or ISO-8601."""
    s = s.strip()
    try:
        return _dt.datetime.strptime(s, "%Y:%m:%d %H:%M:%S")
    except ValueError:
        return _dt.datetime.fromisoformat(s)


def _exif_tag_id(name: str) -> int:
    if not hasattr(piexif.ExifIFD, name):
        raise ValueError(f"Unknown EXIF tag in profile.exif_extras: {name!r}")
    return getattr(piexif.ExifIFD, name)


def _coerce_extra(name: str, value: Any) -> Any:
    """Coerce a JSON-supplied EXIF extra value to what piexif expects.

    Floats become rationals; ints stay ints; strings become bytes;
    1-byte 'undefined' tags (SceneType) become single-byte bytestrings.
    """
    UNDEFINED_BYTE_TAGS = {"SceneType"}
    if name in UNDEFINED_BYTE_TAGS and isinstance(value, int):
        return bytes([value])
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, float):
        return _to_rational(value)
    if isinstance(value, str):
        return value.encode("ascii", errors="replace")
    return value


def build(
    profile: Profile,
    *,
    iso: str = "",
    shutter_speed: str = "",
    exposure_compensation: str = "",
    datetime_taken: str = "",
    pixel_width: int,
    pixel_height: int,
) -> dict[str, dict]:
    """Return a piexif-shaped dict ready for piexif.dump.

    Empty string inputs fall back to the profile defaults.
    Empty datetime_taken → now.
    Caller is responsible for adding GPS and MakerNote if desired.
    """
    iso_val = int(iso) if iso.strip() else int(profile.defaults["iso"])
    shutter_str = shutter_speed.strip() or profile.defaults["shutter"]
    shutter_rational = _parse_shutter(shutter_str)
    exp_comp = (
        float(exposure_compensation)
        if exposure_compensation.strip()
        else float(profile.defaults.get("exposure_compensation", 0.0))
    )
    dt = _parse_dt(datetime_taken) if datetime_taken.strip() else _dt.datetime.now()
    dt_str = dt.strftime("%Y:%m:%d %H:%M:%S").encode("ascii")
    subsec = f"{dt.microsecond // 1000:03d}".encode("ascii")

    zeroth: dict[int, Any] = {
        piexif.ImageIFD.Make: profile.make.encode("ascii"),
        piexif.ImageIFD.Model: profile.model.encode("ascii"),
        piexif.ImageIFD.Software: profile.software.encode("ascii"),
        piexif.ImageIFD.DateTime: dt_str,
        piexif.ImageIFD.Orientation: 1,
        piexif.ImageIFD.XResolution: (72, 1),
        piexif.ImageIFD.YResolution: (72, 1),
        piexif.ImageIFD.ResolutionUnit: 2,
        piexif.ImageIFD.YCbCrPositioning: 1,
    }

    exif: dict[int, Any] = {
        piexif.ExifIFD.ExifVersion: b"0232",
        piexif.ExifIFD.DateTimeOriginal: dt_str,
        piexif.ExifIFD.DateTimeDigitized: dt_str,
        piexif.ExifIFD.SubSecTime: subsec,
        piexif.ExifIFD.SubSecTimeOriginal: subsec,
        piexif.ExifIFD.SubSecTimeDigitized: subsec,
        piexif.ExifIFD.ExposureTime: shutter_rational,
        piexif.ExifIFD.FNumber: _to_rational(profile.aperture),
        piexif.ExifIFD.ISOSpeedRatings: iso_val,
        piexif.ExifIFD.ExposureBiasValue: _to_rational(exp_comp),
        piexif.ExifIFD.FocalLength: _to_rational(profile.focal_length_mm),
        piexif.ExifIFD.FocalLengthIn35mmFilm: profile.focal_length_35mm,
        piexif.ExifIFD.LensMake: profile.lens_make.encode("ascii"),
        piexif.ExifIFD.LensModel: profile.lens_model.encode("ascii"),
        piexif.ExifIFD.LensSpecification: (
            _to_rational(profile.focal_length_mm),
            _to_rational(profile.focal_length_mm),
            _to_rational(profile.aperture),
            _to_rational(profile.aperture),
        ),
        piexif.ExifIFD.PixelXDimension: int(pixel_width),
        piexif.ExifIFD.PixelYDimension: int(pixel_height),
        piexif.ExifIFD.ComponentsConfiguration: b"\x01\x02\x03\x00",
        piexif.ExifIFD.FlashpixVersion: b"0100",
    }

    for name, value in profile.exif_extras.items():
        exif[_exif_tag_id(name)] = _coerce_extra(name, value)

    return {"0th": zeroth, "Exif": exif, "GPS": {}, "1st": {}, "thumbnail": None}
