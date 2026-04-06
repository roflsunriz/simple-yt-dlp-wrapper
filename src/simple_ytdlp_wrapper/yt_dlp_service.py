from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path

from .dependencies import DependencyStatus
from .filename_utils import sanitize_file_basename
from .models import AnalysisResult, DownloadContext, FormatOption, SubtitleOption


THUMBNAIL_URL_RE = re.compile(r"(?P<url>https?://\S+)$")
DOWNLOAD_PROGRESS_RE = re.compile(
    r"\[download\]\s+(?P<percent>\d+(?:\.\d+)?)%\s+of\s+~?(?P<total>\S+)(?:\s+at\s+(?P<speed>\S+)\s+ETA\s+(?P<eta>\S+))?"
)
DESTINATION_RE = re.compile(r"^\[download\]\s+Destination:\s+(?P<path>.+)$")
MERGER_RE = re.compile(r"^\[Merger\]\s+Merging formats into\s+\"(?P<path>.+)\"$")
ALREADY_DOWNLOADED_RE = re.compile(r"^\[download\]\s+(?P<path>.+?) has already been downloaded$")
UNIT_FACTORS = {
    "B": 1,
    "KiB": 1024,
    "MiB": 1024**2,
    "GiB": 1024**3,
    "TiB": 1024**4,
}
CONTAINER_PRIORITY = {"mp4": 3, "m4a": 3, "mkv": 2, "webm": 1}


class YtDlpError(RuntimeError):
    pass


class DownloadCancelledError(YtDlpError):
    pass


def _build_env(ffmpeg_path: str | None) -> dict[str, str]:
    env = os.environ.copy()
    if ffmpeg_path:
        env["PATH"] = f"{Path(ffmpeg_path).parent}{os.pathsep}{env.get('PATH', '')}"
    return env


def _run_command(command: list[str], ffmpeg_path: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=_build_env(ffmpeg_path),
        check=False,
    )


def analyze_url(url: str, dependencies: DependencyStatus) -> AnalysisResult:
    if not dependencies.has_yt_dlp:
        raise YtDlpError("yt-dlp が見つかりません。")

    result = _run_command(
        [dependencies.yt_dlp_path, "--no-playlist", "-J", "--simulate", url],
        dependencies.ffmpeg_path,
    )
    if result.returncode != 0:
        raise YtDlpError(result.stderr.strip() or "URL分析に失敗しました。")

    payload = json.loads(result.stdout)
    if payload.get("_type") == "playlist":
        raise YtDlpError("プレイリスト URL は未対応です。")

    formats = payload.get("formats") or []
    video_formats: list[FormatOption] = []
    audio_formats: list[FormatOption] = []
    for item in formats:
        vcodec = item.get("vcodec", "none")
        acodec = item.get("acodec", "none")
        ext = item.get("ext", "")
        height = int(item.get("height") or 0)
        bitrate = float(item.get("tbr") or item.get("abr") or 0.0)
        if vcodec != "none":
            kind = "統合済み" if acodec != "none" else "映像専用"
            video_formats.append(
                FormatOption(
                    format_id=item.get("format_id", ""),
                    label=f"{item.get('format_id')} | {height or '?'}p | {ext} | {kind}",
                    ext=ext,
                    resolution=height,
                    bitrate=bitrate,
                    kind=kind,
                    has_audio=acodec != "none",
                    has_video=True,
                )
            )
        if acodec != "none":
            abr = int(item.get("abr") or bitrate or 0)
            kind = "統合済み" if vcodec != "none" else "音声専用"
            audio_formats.append(
                FormatOption(
                    format_id=item.get("format_id", ""),
                    label=f"{item.get('format_id')} | {abr}kbps | {ext} | {kind}",
                    ext=ext,
                    resolution=0,
                    bitrate=bitrate,
                    kind=kind,
                    has_audio=True,
                    has_video=vcodec != "none",
                )
            )

    if not video_formats and not audio_formats:
        raise YtDlpError("ダウンロード候補が見つかりません。")

    video_formats.sort(
        key=lambda item: (item.resolution, item.bitrate, CONTAINER_PRIORITY.get(item.ext, 0)),
        reverse=True,
    )
    audio_formats.sort(key=lambda item: item.bitrate, reverse=True)

    return AnalysisResult(
        title=payload.get("title") or "Untitled",
        description=payload.get("description") or "",
        thumbnail_url=_fetch_thumbnail_url(url, dependencies) or payload.get("thumbnail") or "",
        video_formats=video_formats,
        audio_formats=audio_formats,
        subtitles=_extract_subtitles(payload),
        original_url=url,
    )


def _fetch_thumbnail_url(url: str, dependencies: DependencyStatus) -> str:
    result = _run_command(
        [dependencies.yt_dlp_path, "--list-thumbnails", "--no-playlist", url],
        dependencies.ffmpeg_path,
    )
    if result.returncode != 0:
        return ""
    urls = []
    for line in result.stdout.splitlines():
        match = THUMBNAIL_URL_RE.search(line.strip())
        if match:
            urls.append(match.group("url"))
    return urls[-1] if urls else ""


def _extract_subtitles(payload: dict) -> list[SubtitleOption]:
    subtitles: list[SubtitleOption] = []
    seen: set[tuple[str, str, bool]] = set()
    for auto_generated, key in ((False, "subtitles"), (True, "automatic_captions")):
        for language, items in (payload.get(key) or {}).items():
            for item in items:
                ext = item.get("ext", "")
                if ext not in {"srt", "vtt"}:
                    continue
                signature = (language, ext, auto_generated)
                if signature in seen:
                    continue
                seen.add(signature)
                subtitles.append(
                    SubtitleOption(language=language, ext=ext, auto_generated=auto_generated)
                )
    return sorted(
        subtitles,
        key=lambda item: (
            0 if item.language.startswith("ja") else 1 if item.language.startswith("en") else 2,
            0 if item.ext == "srt" else 1,
            1 if item.auto_generated else 0,
        ),
    )


def select_best_video(video_formats: list[FormatOption]) -> FormatOption | None:
    return video_formats[0] if video_formats else None


def select_1080p_video(video_formats: list[FormatOption]) -> FormatOption | None:
    if not video_formats:
        return None
    candidates = [item for item in video_formats if item.resolution and item.resolution <= 1080]
    return candidates[0] if candidates else min(video_formats, key=lambda item: item.resolution or 999999)


def select_best_audio(audio_formats: list[FormatOption]) -> FormatOption | None:
    return audio_formats[0] if audio_formats else None


def choose_subtitle(subtitles: list[SubtitleOption]) -> SubtitleOption | None:
    return subtitles[0] if subtitles else None


def build_download_command(
    dependencies: DependencyStatus,
    analysis: AnalysisResult,
    output_dir: str,
    file_basename: str,
    mode: str,
    video_format_id: str,
    audio_format_id: str,
    container: str,
    download_subtitle: bool,
    embed_subtitle: bool,
    overwrite: bool,
) -> list[str]:
    command = [dependencies.yt_dlp_path, "--newline", "--no-playlist", "-P", output_dir]
    command.append("--force-overwrites" if overwrite else "--no-overwrites")
    command.extend(["-o", f"{sanitize_file_basename(file_basename or analysis.title)}.%(ext)s"])

    if mode == "best":
        video = select_best_video(analysis.video_formats)
        audio = select_best_audio(analysis.audio_formats)
    elif mode == "1080p":
        video = select_1080p_video(analysis.video_formats)
        audio = select_best_audio(analysis.audio_formats)
    else:
        video = next((item for item in analysis.video_formats if item.format_id == video_format_id), None)
        audio = next((item for item in analysis.audio_formats if item.format_id == audio_format_id), None)

    if not video:
        raise YtDlpError("動画フォーマットを選択できません。")

    if video.kind == "映像専用":
        if not audio:
            raise YtDlpError("音声フォーマットを選択できません。")
        if not dependencies.has_ffmpeg:
            raise YtDlpError("ffmpeg が見つからないためマージできません。")
        command.extend(["-f", f"{video.format_id}+{audio.format_id}", "--merge-output-format", container])
    else:
        command.extend(["-f", video.format_id])

    if download_subtitle:
        subtitle = choose_subtitle(analysis.subtitles)
        if subtitle:
            command.extend(["--write-subs", "--sub-langs", subtitle.language, "--convert-subs", subtitle.ext])
            if embed_subtitle:
                command.append("--embed-subs")

    command.append(analysis.original_url)
    return command


def run_download(
    command: list[str],
    dependencies: DependencyStatus,
    on_progress,
    is_cancelled,
    on_output_path=None,
) -> None:
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=_build_env(dependencies.ffmpeg_path),
    )
    try:
        for raw_line in process.stdout or []:
            if is_cancelled():
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
                raise DownloadCancelledError("ダウンロードを中止しました。")

            line = raw_line.strip()
            output_path = _extract_output_path(line)
            if output_path and on_output_path:
                on_output_path(output_path)

            progress = _parse_progress_line(line)
            if progress:
                on_progress(progress)
        return_code = process.wait()
    finally:
        if process.poll() is None:
            process.kill()

    if return_code != 0:
        raise YtDlpError("ダウンロードに失敗しました。")


def _parse_progress_line(line: str) -> dict | None:
    match = DOWNLOAD_PROGRESS_RE.search(line)
    if match:
        percent = float(match.group("percent"))
        total_bytes = _parse_size_to_bytes(match.group("total"))
        downloaded_bytes = int(total_bytes * percent / 100) if total_bytes is not None else None
        remaining_bytes = (
            max(total_bytes - downloaded_bytes, 0)
            if total_bytes is not None and downloaded_bytes is not None
            else None
        )
        return {
            "percent": percent,
            "speed": match.group("speed") or "",
            "eta": match.group("eta") or "",
            "total_bytes": total_bytes,
            "downloaded_bytes": downloaded_bytes,
            "remaining_bytes": remaining_bytes,
            "step": "ダウンロード中",
            "raw": line,
        }
    if line:
        return {
            "percent": None,
            "speed": "",
            "eta": "",
            "total_bytes": None,
            "downloaded_bytes": None,
            "remaining_bytes": None,
            "step": line,
            "raw": line,
        }
    return None


def _parse_size_to_bytes(text: str) -> int | None:
    match = re.fullmatch(r"(?P<value>\d+(?:\.\d+)?)(?P<unit>[KMGTP]?i?B)", text)
    if not match:
        return None
    return int(float(match.group("value")) * UNIT_FACTORS[match.group("unit")])


def format_bytes(num_bytes: int | None) -> str:
    if num_bytes is None:
        return "-"
    size = float(num_bytes)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if size < 1024 or unit == "TiB":
            return f"{size:.1f}{unit}" if unit != "B" else f"{int(size)}B"
        size /= 1024
    return "-"


def _extract_output_path(line: str) -> str | None:
    for pattern in (DESTINATION_RE, MERGER_RE, ALREADY_DOWNLOADED_RE):
        match = pattern.match(line)
        if match:
            return match.group("path")
    return None


def snapshot_existing_paths(output_dir: Path, basename: str) -> set[str]:
    return {str(path.resolve()) for path in output_dir.glob(f"{basename}*") if path.exists()}


def cleanup_cancelled_download(context: DownloadContext) -> list[Path]:
    removed: list[Path] = []
    for path in context.output_dir.glob(f"{context.basename}*"):
        resolved = str(path.resolve())
        if resolved in context.existing_paths:
            continue
        if not path.exists():
            continue
        try:
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
            removed.append(path)
        except OSError:
            continue
    return removed
