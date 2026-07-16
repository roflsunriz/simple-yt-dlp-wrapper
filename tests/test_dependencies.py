from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.simple_ytdlp_wrapper.dependencies import _resolve_command_wrapper


class ResolveCommandWrapperTests(unittest.TestCase):
    def test_resolves_quoted_ffmpeg_executable_from_cmd_wrapper(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            executable = root / "ffmpeg-bin" / "ffmpeg.exe"
            executable.parent.mkdir()
            executable.touch()
            wrapper = root / "ffmpeg.cmd"
            wrapper.write_text(
                f'@echo off\n"{executable}" %*\nexit /b %errorlevel%\n',
                encoding="utf-8",
            )

            resolved = _resolve_command_wrapper(str(wrapper), "ffmpeg")

            self.assertEqual(resolved, str(executable.resolve()))

    def test_rejects_wrapper_without_existing_ffmpeg_executable(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            wrapper = Path(temp_dir) / "ffmpeg.cmd"
            wrapper.write_text('@echo off\n"C:\\missing\\ffmpeg.exe" %*\n', encoding="utf-8")

            self.assertIsNone(_resolve_command_wrapper(str(wrapper), "ffmpeg"))


if __name__ == "__main__":
    unittest.main()
