"""Build a piexif GPS IFD from optional user inputs."""
from __future__ import annotations

import datetime as _dt
from fractions import Fraction
from typing import Any

import piexif


def _to_rational(value: float, max_denom: int = 1_000_000) -> tuple[int, int]:
    f = Fraction(value).limit_denominator(max_denom)
    return f.numerator, f.denominator


def _decimal_to_dms(decimal: float) -> tuple[tuple[int, int], tuple[int, int], tuple[int, int]]:
    """Decimal degrees → (deg, min, sec) as piexif rationals."""
    decimal = abs(decimal)
    deg = int(decimal)
    minutes_float = (decimal - deg) * 60
    minutes = int(minutes_float)
    seconds = (minutes_float - minutes) * 60
    return (deg, 1), (minutes, 1), _to_rational(seconds)


def _f(s: str) -> float:
    return float(s.strip())


def build(
    *,
    latitude: str = "",
    longitude: str = "",
    altitude_m: str = "",
    timestamp: str = "",
    heading_deg: str = "",
    speed_kmh: str = "",
    h_error_m: str = "",
    fallback_datetime: _dt.datetime | None = None,
) -> dict[int, Any]:
    """Return a GPS IFD dict, or {} if lat/lon are not both provided.

    Raises ValueError if exactly one of lat/lon is provided.
    """
    has_lat = bool(latitude.strip())
    has_lon = bool(longitude.strip())
    if has_lat ^ has_lon:
        raise ValueError("GPS latitude and longitude must both be provided, or neither.")
    if not has_lat:
        return {}

    lat = _f(latitude)
    lon = _f(longitude)
    gps: dict[int, Any] = {
        piexif.GPSIFD.GPSVersionID: (2, 3, 0, 0),
        piexif.GPSIFD.GPSLatitudeRef: (b"N" if lat >= 0 else b"S"),
        piexif.GPSIFD.GPSLatitude: _decimal_to_dms(lat),
        piexif.GPSIFD.GPSLongitudeRef: (b"E" if lon >= 0 else b"W"),
        piexif.GPSIFD.GPSLongitude: _decimal_to_dms(lon),
    }

    if altitude_m.strip():
        alt = _f(altitude_m)
        gps[piexif.GPSIFD.GPSAltitudeRef] = 0 if alt >= 0 else 1
        gps[piexif.GPSIFD.GPSAltitude] = _to_rational(abs(alt))

    if heading_deg.strip():
        h = _f(heading_deg) % 360.0
        gps[piexif.GPSIFD.GPSImgDirectionRef] = b"T"
        gps[piexif.GPSIFD.GPSImgDirection] = _to_rational(h)

    if speed_kmh.strip():
        gps[piexif.GPSIFD.GPSSpeedRef] = b"K"
        gps[piexif.GPSIFD.GPSSpeed] = _to_rational(_f(speed_kmh))

    if h_error_m.strip():
        gps[piexif.GPSIFD.GPSHPositioningError] = _to_rational(_f(h_error_m))

    if timestamp.strip():
        try:
            ts_dt = _dt.datetime.strptime(timestamp.strip(), "%Y:%m:%d %H:%M:%S")
        except ValueError:
            ts_dt = _dt.datetime.fromisoformat(timestamp.strip())
    else:
        ts_dt = fallback_datetime or _dt.datetime.now()

    gps[piexif.GPSIFD.GPSDateStamp] = ts_dt.strftime("%Y:%m:%d").encode("ascii")
    gps[piexif.GPSIFD.GPSTimeStamp] = (
        (ts_dt.hour, 1),
        (ts_dt.minute, 1),
        (ts_dt.second, 1),
    )
    return gps
