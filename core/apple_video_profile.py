"""Random iPhone 17 Pro profile for video container metadata.

Python port of influencer-studio-api's AppleDeviceProfile.kt, trimmed to the
fields actually written into the MP4 container by VideoMetadataService.
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

MAKE = "Apple"
MODEL = "iPhone 17 Pro"
IOS_VERSIONS = ["19.0", "19.0.1", "19.1", "19.1.2", "19.2"]


@dataclass
class Gps:
    lat: float
    lon: float
    altitude_meters: float
    img_direction: float

    def iso6709(self) -> str:
        lat = f"{self.lat:+08.4f}"
        lon = f"{self.lon:+09.4f}"
        alt = f"{self.altitude_meters:+08.3f}"
        return f"{lat}{lon}{alt}/"


@dataclass
class AppleVideoProfile:
    make: str
    model: str
    software: str
    capture: datetime
    sub_sec: str
    gps: Optional[Gps]

    def iso_datetime(self) -> str:
        # ISO-8601 with trailing Z, second precision (matches Kotlin format)
        return self.capture.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def random_profile(gps_anchor: Optional[tuple[float, float]] = None) -> AppleVideoProfile:
    minutes_ago = random.randint(5, 60 * 24 * 30)
    capture = datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)
    sub_sec = f"{random.randint(0, 999):03d}"
    software = random.choice(IOS_VERSIONS)

    gps: Optional[Gps] = None
    if gps_anchor is not None:
        lat, lon = gps_anchor
        gps = Gps(
            lat=lat,
            lon=lon,
            altitude_meters=random.uniform(0.0, 200.0),
            img_direction=random.uniform(0.0, 360.0),
        )

    return AppleVideoProfile(
        make=MAKE,
        model=MODEL,
        software=software,
        capture=capture,
        sub_sec=sub_sec,
        gps=gps,
    )
