"""SaveVideoWithEXIF — re-encode a VIDEO with fake iPhone QuickTime metadata."""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from ..core import counter
from ..core.apple_video_profile import random_profile
from ..core.filename_tokens import apply_all

try:
    import folder_paths  # type: ignore
except ImportError:
    folder_paths = None


def _output_dir() -> Path:
    if folder_paths is not None:
        return Path(folder_paths.get_output_directory())
    return Path("output")


def _resolve_ffmpeg() -> str:
    env = os.environ.get("COMFYUI_EXIF_FAKER_FFMPEG")
    if env:
        return env
    found = shutil.which("ffmpeg")
    if found:
        return found
    raise RuntimeError(
        "ffmpeg binary not found in PATH; install ffmpeg or set "
        "COMFYUI_EXIF_FAKER_FFMPEG to the absolute path of the binary."
    )


def _video_dimensions(video) -> tuple[int, int]:
    """Best-effort (width, height) probe for ComfyUI VIDEO inputs."""
    getter = getattr(video, "get_dimensions", None)
    if callable(getter):
        try:
            w, h = getter()
            return int(w), int(h)
        except Exception:
            pass
    try:
        comps = video.get_components()
        # comps.images: tensor [N, H, W, C]
        images = getattr(comps, "images", None)
        if images is not None and hasattr(images, "shape") and len(images.shape) >= 3:
            return int(images.shape[2]), int(images.shape[1])
    except Exception:
        pass
    return 0, 0


class SaveVideoWithEXIF:
    CATEGORY = "image/exif"
    FUNCTION = "execute"
    RETURN_TYPES = ()
    OUTPUT_NODE = True

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "video": ("VIDEO",),
                "filename_prefix": ("STRING", {"default": "IMG"}),
                "crf": ("INT", {"default": 20, "min": 0, "max": 51, "step": 1}),
            },
            "optional": {
                "latitude": ("FLOAT", {"default": 0.0, "min": -90.0, "max": 90.0, "step": 0.000001}),
                "longitude": ("FLOAT", {"default": 0.0, "min": -180.0, "max": 180.0, "step": 0.000001}),
            },
        }

    def execute(
        self,
        video,
        filename_prefix: str,
        crf: int,
        latitude: float = 0.0,
        longitude: float = 0.0,
    ):
        ffmpeg = _resolve_ffmpeg()

        gps_anchor = None
        if latitude != 0.0 and longitude != 0.0:
            gps_anchor = (float(latitude), float(longitude))
        profile = random_profile(gps_anchor)

        width, height = _video_dimensions(video)
        prefix = apply_all(filename_prefix or "IMG", width, height, profile.capture)

        if folder_paths is not None:
            full_output_folder, filename, _, subfolder, _ = folder_paths.get_save_image_path(
                prefix,
                folder_paths.get_output_directory(),
                width or 0,
                height or 0,
            )
            out_dir = Path(full_output_folder)
            out_path = counter.next_path(out_dir, prefix=filename, ext=".MP4")
        else:
            out_dir = _output_dir()
            out_path = counter.next_path(out_dir, prefix=prefix, ext=".MP4")
            try:
                rel = out_path.parent.relative_to(out_dir)
                subfolder = "" if str(rel) == "." else str(rel)
            except ValueError:
                subfolder = ""

        tmp_in_path: Path | None = None
        try:
            tmp_fd, tmp_name = tempfile.mkstemp(suffix=".mp4", prefix="exif_faker_in_")
            os.close(tmp_fd)
            tmp_in_path = Path(tmp_name)
            video.save_to(str(tmp_in_path))

            iso_dt = profile.iso_datetime()
            args = [
                ffmpeg,
                "-hide_banner",
                "-loglevel", "error",
                "-y",
                "-i", str(tmp_in_path),
                "-c:v", "libx264",
                "-profile:v", "high",
                "-level", "5.1",
                "-preset", "medium",
                "-crf", str(int(crf)),
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-b:a", "128k",
                "-movflags", "+faststart+use_metadata_tags",
                "-metadata", f"make={profile.make}",
                "-metadata", f"model={profile.model}",
                "-metadata", f"software={profile.software}",
                "-metadata", f"creation_time={iso_dt}",
                "-metadata", f"com.apple.quicktime.make={profile.make}",
                "-metadata", f"com.apple.quicktime.model={profile.model}",
                "-metadata", f"com.apple.quicktime.software={profile.software}",
                "-metadata", f"com.apple.quicktime.creationdate={iso_dt}",
            ]
            if profile.gps is not None:
                iso6709 = profile.gps.iso6709()
                args += [
                    "-metadata", f"location={iso6709}",
                    "-metadata", f"location-eng={iso6709}",
                    "-metadata", f"com.apple.quicktime.location.ISO6709={iso6709}",
                ]
            args.append(str(out_path))

            result = subprocess.run(args, capture_output=True, check=False, timeout=1800)
            if result.returncode != 0:
                raise RuntimeError(
                    "ffmpeg failed (exit "
                    f"{result.returncode}): {result.stderr.decode('utf-8', errors='replace')}"
                )
        finally:
            if tmp_in_path is not None and tmp_in_path.exists():
                try:
                    tmp_in_path.unlink()
                except OSError:
                    pass

        return {
            "ui": {
                "images": [
                    {"filename": out_path.name, "subfolder": subfolder, "type": "output"}
                ]
            }
        }
