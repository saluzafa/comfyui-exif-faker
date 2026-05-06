# ComfyUI EXIF Faker

Five ComfyUI nodes for working with EXIF metadata on generated images.

## Pipeline

```
[Load Image (with EXIF)] ─┐
                          ▼
                      [EXIF Copy] ──> (IMAGE, EXIF) ──┬─> [Save JPG]
                          ▲                           └─> [Preview JPG]
                          │
[VAE Decode etc.] ────────┘ (target_image)


[VAE Decode etc.] ──> [EXIF Faker] ──> (IMAGE, EXIF) ──┬─> [Save JPG]
                                                       └─> [Preview JPG]
```

`EXIFFaker` and `EXIFCopy` produce metadata; `SaveJPG` and `PreviewJPG` do the I/O. You can branch the same `(IMAGE, EXIF)` pair into both save and preview.

## Nodes

### EXIF Faker (fake camera metadata)
Builds fabricated EXIF that mimics a real device (currently iPhone 15 Pro main 24 mm).

- **Inputs:** `image`, `device_profile` (dropdown), `enable_makernote`
- **Optional per-shot overrides** (empty ⇒ profile default, empty datetime ⇒ now): `iso`, `shutter_speed` (e.g. `1/120`), `exposure_compensation`, `datetime_taken` (`YYYY:MM:DD HH:MM:SS`)
- **Optional GPS** (omit lat+lon ⇒ no GPS block): `gps_latitude`, `gps_longitude`, `gps_altitude_m`, `gps_timestamp`, `gps_heading_deg`, `gps_speed_kmh`, `gps_h_error_m`
- **Outputs:** `IMAGE` (pass-through), `EXIF` (raw bytes ready for SaveJPG/PreviewJPG)

### Load Image (with EXIF)
Like the stock LoadImage but also returns the source file's raw EXIF bytes on a second `EXIF` output.

### EXIF Copy (transfer metadata)
Pairs the target `IMAGE` with EXIF copied verbatim from an `EXIF` source — useful for round-tripping a real photo through a generative workflow without losing its metadata (Apple MakerNote bytes are preserved).

- **Inputs:** `target_image` (IMAGE), `exif_source` (EXIF from LoadImageWithEXIF)
- **Outputs:** `IMAGE` (pass-through), `EXIF` (rewritten with target dimensions)

### Save JPG (with EXIF)
Encodes IMAGE as JPEG with the supplied EXIF and writes `IMG_XXXX.JPG` (4-digit counter) to ComfyUI's output folder.

- **Inputs:** `image`, `exif`, `jpg_quality` (1–100, default 92), `filename_prefix` (default `IMG`)

### Save Video (with EXIF)
Re-encodes a `VIDEO` (e.g. from a Wan/Hunyuan workflow or a `LoadVideo` node) through ffmpeg and embeds randomized iPhone 17 Pro QuickTime metadata, then writes `IMG_XXXX.MP4` to ComfyUI's output folder. Mirrors the algorithm used by the influencer-studio video-authenticity pipeline.

- **Inputs:** `video`, `filename_prefix` (default `IMG`, supports the same `%date:...%`/`%width%`/`%height%` tokens as Save JPG), `crf` (0–51, default 20)
- **Optional GPS:** `latitude`, `longitude` — leave both at `0.0` to skip GPS tags entirely. When set, altitude (0–200 m) and image direction (0–360°) are randomized and `com.apple.quicktime.location.ISO6709` is written.
- Tags written: `make=Apple`, `model=iPhone 17 Pro`, `software` (random iOS 19.x), `creation_time` (random within the last 30 days, ISO-8601 Z), and the matching `com.apple.quicktime.*` atoms.
- **Requires `ffmpeg` on the system PATH** (or set `COMFYUI_EXIF_FAKER_FFMPEG=/path/to/ffmpeg`). Re-encodes with `libx264` high@5.1 / CRF 20 / yuv420p + AAC 128k, `+faststart+use_metadata_tags`.

### Preview JPG (with EXIF)
Encodes IMAGE+EXIF into ComfyUI's temp folder so the JPG appears in the node panel for visual inspection. Re-runs every workflow execution.

- **Inputs:** `image`, `exif`, `jpg_quality` (1–100, default 92)

## Install

```
cd ComfyUI/custom_nodes
git clone <this repo>
pip install -r comfyui-exif-faker/requirements.txt
```

Restart ComfyUI. The five nodes appear under `image/exif`.

## Adding a device profile

Drop a JSON file into `profiles/` matching the shape of `profiles/iphone_15_pro.json`, then restart ComfyUI. The dropdown auto-populates from `display_name` fields.

## Apple MakerNote

For the most authentic iPhone metadata, capture a real MakerNote blob from any iPhone 15 Pro JPG and drop it in:

```
exiftool -MakerNote -b real_iphone_photo.jpg > profiles/iphone_15_pro.makernote.bin
```

Without that file the node still works — it just omits the MakerNote tag (and logs a one-time warning). Per-shot dynamic patching of MakerNote fields (acceleration vector, ContentIdentifier UUID) is a TODO; for now the template bytes are shipped as-is.
