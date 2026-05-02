"""EXIFFaker — build fake EXIF for an IMAGE; emits (IMAGE, EXIF bytes)."""
from __future__ import annotations

import datetime as _dt

import piexif

from ..core import exif_builder, gps_builder, jpeg_writer, makernote, profiles


_PROFILES = profiles.discover()


def _tensor_hw(image) -> tuple[int, int]:
    """Return (height, width) from a ComfyUI IMAGE tensor shape [B,H,W,C]."""
    shape = image.shape if hasattr(image, "shape") else (1, 0, 0, 3)
    return int(shape[1]), int(shape[2])


class EXIFFaker:
    CATEGORY = "image/exif"
    FUNCTION = "execute"
    RETURN_TYPES = ("IMAGE", "EXIF")
    RETURN_NAMES = ("image", "exif")

    @classmethod
    def INPUT_TYPES(cls):
        names = sorted(_PROFILES.keys()) or ["<no profiles found>"]
        return {
            "required": {
                "image": ("IMAGE",),
                "device_profile": (names,),
                "enable_makernote": ("BOOLEAN", {"default": True}),
            },
            "optional": {
                "iso": ("STRING", {"default": ""}),
                "shutter_speed": ("STRING", {"default": ""}),
                "exposure_compensation": ("STRING", {"default": ""}),
                "datetime_taken": ("STRING", {"default": ""}),
                "gps_latitude": ("STRING", {"default": ""}),
                "gps_longitude": ("STRING", {"default": ""}),
                "gps_altitude_m": ("STRING", {"default": ""}),
                "gps_timestamp": ("STRING", {"default": ""}),
                "gps_heading_deg": ("STRING", {"default": ""}),
                "gps_speed_kmh": ("STRING", {"default": ""}),
                "gps_h_error_m": ("STRING", {"default": ""}),
            },
        }

    def execute(
        self,
        image,
        device_profile: str,
        enable_makernote: bool,
        iso: str = "",
        shutter_speed: str = "",
        exposure_compensation: str = "",
        datetime_taken: str = "",
        gps_latitude: str = "",
        gps_longitude: str = "",
        gps_altitude_m: str = "",
        gps_timestamp: str = "",
        gps_heading_deg: str = "",
        gps_speed_kmh: str = "",
        gps_h_error_m: str = "",
    ):
        if device_profile not in _PROFILES:
            raise ValueError(f"Unknown device profile: {device_profile!r}")
        profile = _PROFILES[device_profile]

        capture_dt = (
            exif_builder._parse_dt(datetime_taken)
            if datetime_taken.strip()
            else _dt.datetime.now()
        )
        height, width = _tensor_hw(image)

        exif_dict = exif_builder.build(
            profile,
            iso=iso,
            shutter_speed=shutter_speed,
            exposure_compensation=exposure_compensation,
            datetime_taken=capture_dt.strftime("%Y:%m:%d %H:%M:%S"),
            pixel_width=width,
            pixel_height=height,
        )

        gps = gps_builder.build(
            latitude=gps_latitude,
            longitude=gps_longitude,
            altitude_m=gps_altitude_m,
            timestamp=gps_timestamp,
            heading_deg=gps_heading_deg,
            speed_kmh=gps_speed_kmh,
            h_error_m=gps_h_error_m,
            fallback_datetime=capture_dt,
        )
        if gps:
            exif_dict["GPS"] = gps

        if enable_makernote:
            blob = makernote.load(
                profile.makernote_path,
                profile.makernote.get("dynamic_fields"),
            )
            if blob:
                exif_dict["Exif"][piexif.ExifIFD.MakerNote] = blob

        exif_bytes = jpeg_writer.dump_exif_for_size(exif_dict, width, height)
        return (image, exif_bytes)
