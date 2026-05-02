"""EXIFFaker ComfyUI node."""
from __future__ import annotations

import datetime as _dt
from pathlib import Path

import piexif

from ..core import counter, exif_builder, gps_builder, jpeg_writer, makernote, profiles

try:
    import folder_paths  # type: ignore
except ImportError:  # outside ComfyUI (tests, linting)
    folder_paths = None


_PROFILES = profiles.discover()


def _output_dir() -> Path:
    if folder_paths is not None:
        return Path(folder_paths.get_output_directory())
    return Path("output")


class EXIFFaker:
    CATEGORY = "image/exif"
    FUNCTION = "execute"
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    OUTPUT_NODE = True

    @classmethod
    def INPUT_TYPES(cls):
        names = sorted(_PROFILES.keys()) or ["<no profiles found>"]
        return {
            "required": {
                "image": ("IMAGE",),
                "device_profile": (names,),
                "jpg_quality": ("INT", {"default": 92, "min": 1, "max": 100, "step": 1}),
                "enable_makernote": ("BOOLEAN", {"default": True}),
                "filename_prefix": ("STRING", {"default": "IMG"}),
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
        jpg_quality: int,
        enable_makernote: bool,
        filename_prefix: str,
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
        dt_str_for_builder = capture_dt.strftime("%Y:%m:%d %H:%M:%S")

        # First pass: build EXIF with placeholder dimensions; jpeg_writer fixes them.
        exif_dict = exif_builder.build(
            profile,
            iso=iso,
            shutter_speed=shutter_speed,
            exposure_compensation=exposure_compensation,
            datetime_taken=dt_str_for_builder,
            pixel_width=0,
            pixel_height=0,
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

        out_path = counter.next_path(_output_dir(), prefix=filename_prefix or "IMG")
        # Save once with quality but without final EXIF dimensions, then re-encode.
        # Simpler: render PIL once, dump EXIF for known size, save.
        from ..core.jpeg_writer import tensor_to_pil
        pil = tensor_to_pil(image)
        exif_bytes = jpeg_writer.dump_exif_for_size(exif_dict, pil.width, pil.height)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        pil.save(out_path, format="JPEG", quality=int(jpg_quality), subsampling=2, exif=exif_bytes)

        return (image,)
