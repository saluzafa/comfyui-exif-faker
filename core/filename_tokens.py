"""Shared filename_prefix token substitution: %date:...%, %width%, %height%."""
from __future__ import annotations

import datetime
import re

_DATE_TOKENS = [
    ("yyyy", "%Y"),
    ("yy", "%y"),
    ("MM", "%m"),
    ("dd", "%d"),
    ("hh", "%H"),
    ("mm", "%M"),
    ("ss", "%S"),
]
_DATE_RE = re.compile(r"%date:([^%]+)%")


def _apply_date(fmt: str, when: datetime.datetime) -> str:
    out = fmt
    sentinels: list[tuple[str, str]] = []
    for i, (tok, strf) in enumerate(_DATE_TOKENS):
        sentinel = f"\x00{i}\x00"
        if tok in out:
            out = out.replace(tok, sentinel)
            sentinels.append((sentinel, strf))
    for sentinel, strf in sentinels:
        out = out.replace(sentinel, when.strftime(strf))
    return out


def apply_date_tokens(prefix: str, when: datetime.datetime) -> str:
    return _DATE_RE.sub(lambda m: _apply_date(m.group(1), when), prefix)


def apply_size_tokens(prefix: str, width: int, height: int) -> str:
    return prefix.replace("%width%", str(width)).replace("%height%", str(height))


def apply_all(prefix: str, width: int, height: int, when: datetime.datetime | None = None) -> str:
    when = when or datetime.datetime.now()
    return apply_date_tokens(apply_size_tokens(prefix, width, height), when)
