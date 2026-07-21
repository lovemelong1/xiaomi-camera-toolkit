from __future__ import annotations

import argparse
import os
import time
from datetime import datetime, timedelta
from pathlib import Path

from .cleanup import can_delete_day, delete_sources, remove_empty_dirs
from .formats import group_by_day, scan_segments
from .merge import build_daily_video
from .timelapse import build_timelapse


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "y", "on"}


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Xiaomi camera multi-format timelapse and daily merge tool")
    p.add_argument("--input", default=os.getenv("INPUT_DIR", "/data/input"))
    p.add_argument("--output", default=os.getenv("OUTPUT_DIR", "/data/output"))
    p.add_argument("--mode", choices=["timelapse", "merge-day", "both"], default=os.getenv("MODE", "timelapse"))
    p.add_argument("--run-mode", choices=["once", "scheduler"], default=os.getenv("RUN_MODE", "once"))
    p.add_argument("--schedule-time", default=os.getenv("SCHEDULE_TIME", "03:00"))
    p.add_argument("--interval-days", type=int, default=int(os.getenv("INTERVAL_DAYS", "1")))
    p.add_argument("--target-day", default=os.getenv("TARGET_DAY"))
    p.add_argument("--target-lag-days", type=int, default=int(os.getenv("TARGET_LAG_DAYS", "1")))
    p.add_argument("--frames", type=int, default=int(os.getenv("FRAMES", "30")))
    p.add_argument("--fps", type=int, default=int(os.getenv("FPS", "3")))
    p.add_argument("--width", type=int, default=int(os.getenv("WIDTH", "1280")))
    p.add_argument("--merge-crf", type=int, default=int(os.getenv("MERGE_CRF", "32")))
    p.add_argument("--delete-source", action="store_true", default=env_bool("DELETE_SOURCE", False))
    p.add_argument("--keep-days", type=int, default=int(os.getenv("KEEP_DAYS")) if os.getenv("KEEP_DAYS") else None)
    p.add_argument("--delete-empty-dirs", action="store_true", default=env_bool("DELETE_EMPTY_DIRS", True))
    p.add_argument("--overwrite", action="store_true", default=env_bool("OVERWRITE", False))
    p.add_argument("--dry-run", action="store_true", default=env_bool("DRY_RUN", False))
    return p


def run_once(args: argparse.Namespace) -> int:
    input_root = Path(args.input)
    output_root = Path(args.output)
    segments = scan_segments(input_root)
    grouped = group_by_day(segments)
    all_days = list(grouped)
    target_day_label = args.target_day
    if args.target_day:
        process_days = [args.target_day] if args.target_day in grouped else []
    elif args.run_mode == "scheduler":
        target_day_label = (datetime.now() - timedelta(days=args.target_lag_days)).strftime("%Y%m%d")
        process_days = [target_day_label] if target_day_label in grouped else []
    else:
        process_days = all_days

    print(
        f"found {len(segments)} segments in {len(grouped)} days; "
        f"target_day={target_day_label or 'all'} process_days={len(process_days)}",
        flush=True,
    )
    if target_day_label and not process_days:
        print(f"no source files for target_day={target_day_label}", flush=True)

    success_days: set[str] = set()
    for day in process_days:
        day_segments = grouped[day]
        ok = True
        if args.mode in {"timelapse", "both"}:
            ok = build_timelapse(
                day,
                day_segments,
                output_root,
                frames=args.frames,
                fps=args.fps,
                width=args.width,
                overwrite=args.overwrite,
                dry_run=args.dry_run,
            ) is not None and ok
        if args.mode in {"merge-day", "both"}:
            ok = build_daily_video(
                day,
                day_segments,
                output_root,
                overwrite=args.overwrite,
                dry_run=args.dry_run,
                crf=args.merge_crf,
                width=args.width,
            ) is not None and ok
        if ok:
            success_days.add(day)
    cleanup_days = set(success_days)
    if args.delete_source:
        for day in all_days:
            output = output_root / "延时摄影" / day[:6] / f"{day}.mp4"
            if can_delete_day(day, args.keep_days) and output.exists():
                cleanup_days.add(day)
        for day in sorted(cleanup_days):
            if can_delete_day(day, args.keep_days):
                count = delete_sources(grouped[day], dry_run=args.dry_run)
                print(f"deleted {count} source files for {day}", flush=True)

    if args.delete_source and args.delete_empty_dirs:
        remove_empty_dirs(input_root, dry_run=args.dry_run)
    print(f"done: {len(success_days)} successful days", flush=True)
    return 0


def _sleep_until_next(schedule_time: str, interval_days: int) -> None:
    hour, minute = [int(part) for part in schedule_time.split(":", 1)]
    now = datetime.now()
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=max(interval_days, 1))
    seconds = max((target - now).total_seconds(), 1)
    print(f"next run: {target:%Y-%m-%d %H:%M:%S}", flush=True)
    time.sleep(seconds)


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.run_mode == "once":
        return run_once(args)

    while True:
        run_once(args)
        _sleep_until_next(args.schedule_time, args.interval_days)
