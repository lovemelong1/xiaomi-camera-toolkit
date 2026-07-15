from __future__ import annotations

import tempfile
from pathlib import Path

from .ffmpeg import run_command, valid_video
from .models import Segment


def build_daily_video(
    day: str,
    segments: list[Segment],
    output_root: Path,
    overwrite: bool = False,
    dry_run: bool = False,
    crf: int = 32,
    width: int = 1280,
) -> Path | None:
    month = day[:6]
    output = output_root / "日期录像" / month / f"{day}.mp4"
    if output.exists() and not overwrite and valid_video(output):
        print(f"exists: {output}", flush=True)
        return output

    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as handle:
        list_file = Path(handle.name)
        for segment in segments:
            escaped = str(segment.path).replace("'", "'\\''")
            handle.write(f"file '{escaped}'\n")

    try:
        args = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(list_file),
            "-vf",
            f"scale={width}:-2",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            str(crf),
            "-an",
            "-movflags",
            "+faststart",
            str(output),
        ]
        run_command(args, dry_run=dry_run)
        if dry_run or valid_video(output):
            print(f"daily video ok: {output}", flush=True)
            return output
        print(f"invalid output: {output}", flush=True)
        return None
    finally:
        list_file.unlink(missing_ok=True)
