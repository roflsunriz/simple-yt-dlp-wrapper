from __future__ import annotations

import json
import subprocess
import unittest
from unittest.mock import patch

from src.simple_ytdlp_wrapper.dependencies import DependencyStatus
from src.simple_ytdlp_wrapper.yt_dlp_service import analyze_url, build_download_command


class AnalyzeUrlCodecFallbackTests(unittest.TestCase):
    def setUp(self) -> None:
        self.dependencies = DependencyStatus(yt_dlp_path="yt-dlp", ffmpeg_path=None)
        self.payload = {
            "title": "sample",
            "description": "",
            "thumbnail": "https://example.com/thumb.jpg",
            "formats": [
                {
                    "format_id": "http",
                    "ext": "mp4",
                    "video_ext": "mp4",
                    "audio_ext": "none",
                    "format": "http - unknown",
                    "url": "https://video.twimg.com/sample.mp4",
                }
            ],
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

    def test_build_download_command_for_audio_only_adds_extract_audio_options(self) -> None:
        self.payload["formats"].append(
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


if __name__ == "__main__":
    unittest.main()
