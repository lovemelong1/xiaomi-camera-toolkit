from __future__ import annotations

import shutil
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

from .ffmpeg import run_command, valid_video
from .models import Segment


def weighted_targets(day: str, frames: int) -> list[datetime]:
    date = datetime.strptime(day, "%Y%m%d")
    bands = [
        (0, 6, 0.2),
        (6, 18, 1.0),
        (18, 24, 0.5),
    ]
    slots: list[datetime] = []
    weighted_seconds = sum((end - start) * 3600 * weight for start, end, weight in bands)
    step = weighted_seconds / max(frames, 1)

    for index in range(frames):
        cursor = (index + 0.5) * step
        for start, end, weight in bands:
            band_seconds = (end - start) * 3600 * weight
            if cursor <= band_seconds or end == 24:
                real_seconds = cursor / weight if weight else 0
                slots.append(date + timedelta(hours=start, seconds=real_seconds))
                break
            cursor -= band_seconds
    return slots


def _distance(segment: Segment, target: datetime) -> float:
    if segment.end and segment.start <= target <= segment.end:
        return 0
    return abs((segment.start - target).total_seconds())


def _candidates(segments: list[Segment], target: datetime) -> list[Segment]:
    return sorted(segments, key=lambda segment: (_distance(segment, target), segment.start))


def _extract_frame(segment: Segment, output: Path, dry_run: bool = False) -> bool:
    args = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(segment.path),
        "-frames:v",
        "1",
        "-q:v",
        "4",
        str(output),
    ]
    try:
        run_command(args, dry_run=dry_run)
        return dry_run or output.exists()
    except Exception as exc:
        print(f"skip bad segment: {segment.path} ({exc})", flush=True)
        return False


def build_timelapse(
    day: str,
    segments: list[Segment],
    output_root: Path,
    frames: int,
    fps: int,
    width: int,
    overwrite: bool = False,
    dry_run: bool = False,
    max_frame_attempts: int = 8,
) -> Path | None:
    month = day[:6]
    output = output_root / "延时摄影" / month / f"{day}.mp4"
    if output.exists() and not overwrite and valid_video(output):
        print(f"exists: {output}", flush=True)
        return output

    output.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix=f"xiaomi-{day}-"))
    try:
        made = 0
        for index, target in enumerate(weighted_targets(day, frames), start=1):
            frame = tmp / f"frame_{index:04d}.jpg"
            for segment in _candidates(segments, target)[:max_frame_attempts]:
                if _extract_frame(segment, frame, dry_run=dry_run):
                    made += 1
                    break
        if made == 0:
            print(f"no frames: {day}", flush=True)
            return None

        args = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-framerate",
            str(fps),
            "-pattern_type",
            "glob",
            "-i",
            str(tmp / "frame_*.jpg"),
            "-vf",
            f"scale={width}:-2",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "28",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(output),
        ]
        run_command(args, dry_run=dry_run)
        if dry_run or valid_video(output):
            print(f"timelapse ok: {output} ({made} frames)", flush=True)
            return output
        print(f"invalid output: {output}", flush=True)
        return None
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
