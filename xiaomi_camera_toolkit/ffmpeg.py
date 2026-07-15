from __future__ import annotations

import json
import subprocess
from pathlib import Path


def run_command(args: list[str], dry_run: bool = False) -> None:
    print("+ " + " ".join(args), flush=True)
    if dry_run:
        return
    subprocess.run(args, check=True)


def ffprobe_duration(path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    data = json.loads(result.stdout or "{}")
    return float(data.get("format", {}).get("duration") or 0)


def valid_video(path: Path, min_seconds: float = 1.0) -> bool:
    if not path.exists() or path.stat().st_size < 1024:
        return False
    try:
        return ffprobe_duration(path) >= min_seconds
    except Exception:
        return False
