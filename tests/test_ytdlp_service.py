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
            download_subtitle=False,
            embed_subtitle=False,
            overwrite=False,
        )

        self.assertIn("-f", command)
        self.assertIn("http", command)


if __name__ == "__main__":
    unittest.main()
