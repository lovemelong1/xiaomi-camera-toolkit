from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path

from .models import Segment


def can_delete_day(day: str, keep_days: int | None) -> bool:
    if keep_days is None:
        return True
    day_date = datetime.strptime(day, "%Y%m%d").date()
    return day_date < date.today() - timedelta(days=keep_days)


def delete_sources(segments: list[Segment], dry_run: bool = False) -> int:
    deleted = 0
    for segment in segments:
        if dry_run:
            print(f"would delete: {segment.path}", flush=True)
            deleted += 1
            continue
        try:
            segment.path.unlink()
            deleted += 1
        except FileNotFoundError:
            pass
    return deleted


def remove_empty_dirs(root: Path, dry_run: bool = False) -> None:
    dirs = sorted((path for path in root.rglob("*") if path.is_dir()), key=lambda p: len(p.parts), reverse=True)
    for path in dirs:
        try:
            if any(path.iterdir()):
                continue
            if dry_run:
                print(f"would rmdir: {path}", flush=True)
            else:
                path.rmdir()
        except OSError:
            continue
