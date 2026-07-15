from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class Segment:
    path: Path
    start: datetime
    end: datetime | None = None
    format_name: str = "unknown"

    @property
    def day(self) -> str:
        return self.start.strftime("%Y%m%d")

    @property
    def month(self) -> str:
        return self.start.strftime("%Y%m")
