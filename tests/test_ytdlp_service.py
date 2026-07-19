from __future__ import annotations

import json
import subprocess
import unittest
from unittest.mock import Mock, patch

from src.simple_ytdlp_wrapper.dependencies import DependencyStatus
from src.simple_ytdlp_wrapper.yt_dlp_service import (
    YtDlpError,
    analyze_url,
    build_download_command,
    run_download,
)


class AnalyzeUrlCodecFallbackTests(unittest.TestCase):
    def setUp(self) -> None:
        self.dependencies = DependencyStatus(yt_dlp_path="yt-dlp", ffmpeg_path=None)
        self.formats: list[dict[str, object]] = [
            {
                "format_id": "http",
                "ext": "mp4",
                "video_ext": "mp4",
                "audio_ext": "none",
                "format": "http - unknown",
                "url": "https://video.twimg.com/sample.mp4",
            }
        ]
        self.payload: dict[str, object] = {
            "title": "sample",
            "description": "",
            "thumbnail": "https://example.com/thumb.jpg",
            "formats": self.formats,
            "subtitles": {},
            "automatic_captions": {},
        }

    def _completed(self) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=["yt-dlp"],
            returncode=0,
            stdout=json.dumps(self.payload),
            stderr="",
        )

    def test_analyze_url_accepts_formats_without_codec_fields(self) -> None:
        with (
            patch("src.simple_ytdlp_wrapper.yt_dlp_service._run_command", return_value=self._completed()),
            patch("src.simple_ytdlp_wrapper.yt_dlp_service._fetch_thumbnail_url", return_value=""),
        ):
            result = analyze_url("https://x.com/example/status/1", self.dependencies)

        self.assertEqual(len(result.video_formats), 1)
        self.assertEqual(result.video_formats[0].format_id, "http")
        self.assertEqual(result.video_formats[0].kind, "動画のみ")
        self.assertFalse(result.video_formats[0].requires_merge)

    def test_build_download_command_uses_direct_video_format(self) -> None:
        with (
            patch("src.simple_ytdlp_wrapper.yt_dlp_service._run_command", return_value=self._completed()),
            patch("src.simple_ytdlp_wrapper.yt_dlp_service._fetch_thumbnail_url", return_value=""),
        ):
            analysis = analyze_url("https://x.com/example/status/1", self.dependencies)

        command = build_download_command(
            dependencies=self.dependencies,
            analysis=analysis,
            output_dir="C:\\Downloads",
            file_basename="sample",
            mode="best",
            video_format_id="",
            audio_format_id="",
            container="mp4",
            audio_output_format="mp3",
            audio_codec="auto",
            audio_sample_rate="auto",
            audio_bitrate="auto",
            download_subtitle=False,
            embed_subtitle=False,
            overwrite=False,
        )

        self.assertIn("-f", command)
        self.assertIn("http", command)

    def test_build_download_command_preserves_confirmed_filename_length(self) -> None:
        with (
            patch("src.simple_ytdlp_wrapper.yt_dlp_service._run_command", return_value=self._completed()),
            patch("src.simple_ytdlp_wrapper.yt_dlp_service._fetch_thumbnail_url", return_value=""),
        ):
            analysis = analyze_url("https://x.com/example/status/1", self.dependencies)
        filename = "a" * 40

        command = build_download_command(
            dependencies=self.dependencies,
            analysis=analysis,
            output_dir="C:\\Downloads",
            file_basename=filename,
            mode="best",
            video_format_id="",
            audio_format_id="",
            container="mp4",
            audio_output_format="mp3",
            audio_codec="auto",
            audio_sample_rate="auto",
            audio_bitrate="auto",
            download_subtitle=False,
            embed_subtitle=False,
            overwrite=False,
        )

        self.assertIn(f"{filename}.%(ext)s", command)

    def test_build_download_command_for_audio_only_adds_extract_audio_options(self) -> None:
        self.formats.append(
            {
                "format_id": "251",
                "ext": "webm",
                "acodec": "opus",
                "vcodec": "none",
                "abr": 160,
                "language": "ja",
            }
        )
        dependencies = DependencyStatus(yt_dlp_path="yt-dlp", ffmpeg_path="C:\\ffmpeg\\bin\\ffmpeg.exe")
        with (
            patch("src.simple_ytdlp_wrapper.yt_dlp_service._run_command", return_value=self._completed()),
            patch("src.simple_ytdlp_wrapper.yt_dlp_service._fetch_thumbnail_url", return_value=""),
        ):
            analysis = analyze_url("https://x.com/example/status/1", dependencies)

        command = build_download_command(
            dependencies=dependencies,
            analysis=analysis,
            output_dir="C:\\Downloads",
            file_basename="sample",
            mode="audio_only",
            video_format_id="",
            audio_format_id="",
            container="mp4",
            audio_output_format="mp3",
            audio_codec="libmp3lame",
            audio_sample_rate="44100",
            audio_bitrate="192K",
            download_subtitle=False,
            embed_subtitle=False,
            overwrite=False,
        )

        self.assertIn("-x", command)
        self.assertIn("--audio-format", command)
        self.assertIn("mp3", command)
        self.assertIn("--audio-quality", command)
        self.assertIn("192K", command)
        self.assertIn("--postprocessor-args", command)
        self.assertTrue(any("ExtractAudio+ffmpeg_o:-acodec libmp3lame -ar 44100 -b:a 192k" == item for item in command))

    def test_merge_command_passes_resolved_ffmpeg_location(self) -> None:
        self.formats[:] = [
            {
                "format_id": "hls-video",
                "ext": "mp4",
                "vcodec": "avc1.640032",
                "acodec": "none",
                "video_ext": "mp4",
                "audio_ext": "none",
                "height": 1080,
                "tbr": 8500,
            },
            {
                "format_id": "hls-audio",
                "ext": "mp4",
                "vcodec": "none",
                "acodec": None,
                "video_ext": "none",
                "audio_ext": "mp4",
                "abr": 128,
            },
        ]
        ffmpeg_path = "C:\\ffmpeg\\bin\\ffmpeg.exe"
        dependencies = DependencyStatus(yt_dlp_path="yt-dlp", ffmpeg_path=ffmpeg_path)
        with (
            patch("src.simple_ytdlp_wrapper.yt_dlp_service._run_command", return_value=self._completed()),
            patch("src.simple_ytdlp_wrapper.yt_dlp_service._fetch_thumbnail_url", return_value=""),
        ):
            analysis = analyze_url("https://x.com/example/status/1", dependencies)

        command = build_download_command(
            dependencies=dependencies,
            analysis=analysis,
            output_dir="C:\\Downloads",
            file_basename="sample",
            mode="best",
            video_format_id="",
            audio_format_id="",
            container="mp4",
            audio_output_format="mp3",
            audio_codec="auto",
            audio_sample_rate="auto",
            audio_bitrate="auto",
            download_subtitle=False,
            embed_subtitle=False,
            overwrite=False,
        )

        self.assertIn("hls-video+hls-audio", command)
        location_index = command.index("--ffmpeg-location")
        self.assertEqual(command[location_index + 1], ffmpeg_path)

    def test_merge_warning_is_not_reported_as_success(self) -> None:
        process = Mock()
        process.stdout = ["WARNING: ffmpeg not found. The downloaded formats will not be merged.\n"]
        process.wait.return_value = 0
        process.poll.return_value = 0
        dependencies = DependencyStatus(yt_dlp_path="yt-dlp", ffmpeg_path="C:\\ffmpeg.cmd")

        with patch("src.simple_ytdlp_wrapper.yt_dlp_service.subprocess.Popen", return_value=process):
            with self.assertRaises(YtDlpError) as context:
                run_download(
                    ["yt-dlp", "-f", "video+audio", "--merge-output-format", "mp4", "https://example.com"],
                    dependencies,
                    on_progress=lambda _payload: None,
                    is_cancelled=lambda: False,
                )

        self.assertEqual(context.exception.code, "missing_ffmpeg")
        self.assertIn("ffmpeg not found", context.exception.details)


if __name__ == "__main__":
    unittest.main()
