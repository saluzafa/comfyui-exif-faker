# ComfyUI EXIF Faker

Three ComfyUI nodes for working with EXIF metadata on generated images.

## Nodes

### EXIF Faker (fake camera metadata)
Saves an `IMAGE` as a JPG with fabricated EXIF that mimics a real device (currently iPhone 15 Pro main 24 mm). Pass-through: also returns the input image so you can chain to a preview.

Inputs:
- `image`, `device_profile` (dropdown), `jpg_quality` (1–100, default 92), `enable_makernote`, `filename_prefix`
- Optional per-shot overrides (empty ⇒ profile default, empty datetime ⇒ now): `iso`, `shutter_speed` (e.g. `1/120`), `exposure_compensation`, `datetime_taken` (`YYYY:MM:DD HH:MM:SS`)
- Optional GPS (omit lat+lon ⇒ no GPS block): `gps_latitude`, `gps_longitude`, `gps_altitude_m`, `gps_timestamp`, `gps_heading_deg`, `gps_speed_kmh`, `gps_h_error_m`

Output: `IMG_XXXX.JPG` (4-digit counter) in ComfyUI's `output/` folder.

### Load Image (with EXIF)
Like the stock LoadImage but also returns the source file's raw EXIF bytes on a second `EXIF` output.

### EXIF Copy (transfer metadata)
Saves a target `IMAGE` as a JPG with EXIF copied verbatim from an `EXIF` source — useful for round-tripping a real photo through a generative workflow without losing its metadata (Apple MakerNote bytes are preserved).

## Install

```
cd ComfyUI/custom_nodes
git clone <this repo>
pip install piexif
```

Restart ComfyUI. The three nodes appear under `image/exif`.

## Adding a device profile

Drop a JSON file into `profiles/` matching the shape of `profiles/iphone_15_pro.json`, then restart ComfyUI. The dropdown auto-populates from `display_name` fields.

## Apple MakerNote

For the most authentic iPhone metadata, capture a real MakerNote blob from any iPhone 15 Pro JPG and drop it in:

```
exiftool -MakerNote -b real_iphone_photo.jpg > profiles/iphone_15_pro.makernote.bin
```

Without that file the node still works — it just omits the MakerNote tag (and logs a one-time warning). Per-shot dynamic patching of MakerNote fields (acceleration vector, ContentIdentifier UUID) is a TODO; for now the template bytes are shipped as-is.
