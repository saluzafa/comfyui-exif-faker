"""IMG_XXXX.JPG filename counter that scans the output folder at save time."""
from __future__ import annotations

import re
from pathlib import Path


def next_path(
    output_dir: Path,
    prefix: str = "IMG",
    pad: int = 4,
    ext: str = ".JPG",
) -> Path:
    """Return the next available PREFIX_XXXX<ext> path in output_dir."""
    output_dir.mkdir(parents=True, exist_ok=True)
    ext_re = re.escape(ext)
    pattern = re.compile(rf"^{re.escape(prefix)}_(\d+){ext_re}$", re.IGNORECASE)
    highest = 0
    for f in output_dir.iterdir():
        m = pattern.match(f.name)
        if m:
            highest = max(highest, int(m.group(1)))
    return output_dir / f"{prefix}_{highest + 1:0{pad}d}{ext}"
