from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class FormatOption:
    format_id: str
    label: str
    ext: str
    resolution: int
    bitrate: float
    kind: str
    has_audio: bool = False
    has_video: bool = False


@dataclass
class SubtitleOption:
    language: str
    ext: str
    auto_generated: bool = False


@dataclass
class AnalysisResult:
    title: str
    description: str
    thumbnail_url: str
    video_formats: list[FormatOption] = field(default_factory=list)
    audio_formats: list[FormatOption] = field(default_factory=list)
    subtitles: list[SubtitleOption] = field(default_factory=list)
    original_url: str = ""


@dataclass
class DownloadContext:
    output_dir: Path
    basename: str
    existing_paths: set[str] = field(default_factory=set)
