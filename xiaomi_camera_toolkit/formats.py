from __future__ import annotations

import re
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

from .models import Segment

FLAT_INTERVAL_RE = re.compile(r"^00_(\d{14})_(\d{14})\.mp4$", re.IGNORECASE)
HOUR_DIR_RE = re.compile(r"^\d{10}$")
MINUTE_EPOCH_RE = re.compile(r"^(\d{2})M(\d{2})S_(\d{9,11})\.mp4$", re.IGNORECASE)


def parse_segment(path: Path) -> Segment | None:
    """Parse one supported Xiaomi camera segment path."""
    name = path.name

    flat = FLAT_INTERVAL_RE.match(name)
    if flat:
        start = datetime.strptime(flat.group(1), "%Y%m%d%H%M%S")
        end = datetime.strptime(flat.group(2), "%Y%m%d%H%M%S")
        return Segment(path=path, start=start, end=end, format_name="flat_interval")

    parent = path.parent.name
    minute = MINUTE_EPOCH_RE.match(name)
    if minute and HOUR_DIR_RE.match(parent):
        hour_start = datetime.strptime(parent, "%Y%m%d%H")
        start = hour_start + timedelta(minutes=int(minute.group(1)), seconds=int(minute.group(2)))
        return Segment(path=path, start=start, end=None, format_name="hourly_epoch")

    return None


def scan_segments(root: Path) -> list[Segment]:
    segments: list[Segment] = []
    for path in root.rglob("*.mp4"):
        segment = parse_segment(path)
        if segment is not None:
            segments.append(segment)
    segments.sort(key=lambda item: (item.start, str(item.path)))
    return segments


def group_by_day(segments: list[Segment]) -> dict[str, list[Segment]]:
    grouped: dict[str, list[Segment]] = defaultdict(list)
    for segment in segments:
        grouped[segment.day].append(segment)
    return dict(sorted(grouped.items()))
