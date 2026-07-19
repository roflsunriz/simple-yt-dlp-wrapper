from __future__ import annotations

import logging
import os
import tempfile
import unittest
from typing import ClassVar, cast
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from src.simple_ytdlp_wrapper.config import AppSettings, SettingsLoadResult
from src.simple_ytdlp_wrapper.dependencies import DependencyStatus
from src.simple_ytdlp_wrapper.main_window import MainWindow


class MainWindowOutputDirectoryTests(unittest.TestCase):
    application: ClassVar[QApplication]

    @classmethod
    def setUpClass(cls) -> None:
        application = QApplication.instance()
        cls.application = QApplication([]) if application is None else cast(QApplication, application)

    def setUp(self) -> None:
        logger = logging.getLogger(f"test_main_window_{id(self)}")
        with (
            patch(
                "src.simple_ytdlp_wrapper.main_window.AppSettings.load",
                return_value=SettingsLoadResult(AppSettings.defaults()),
            ),
            patch(
                "src.simple_ytdlp_wrapper.main_window.detect_dependencies",
                return_value=DependencyStatus("yt-dlp", "ffmpeg"),
            ),
            patch("src.simple_ytdlp_wrapper.main_window.configure_logging", return_value=logger),
        ):
            self.window = MainWindow()

    def tearDown(self) -> None:
        self.window.deleteLater()

    def test_open_output_button_opens_selected_directory(self) -> None:
        with tempfile.TemporaryDirectory() as output_dir:
            self.window.output_dir_input.setText(output_dir)
            with patch("src.simple_ytdlp_wrapper.main_window.os.startfile", create=True) as startfile:
                self.window.open_output_button.click()

        startfile.assert_called_once_with(output_dir)

    def test_open_output_button_remains_available_while_downloading(self) -> None:
        self.window._set_state("ダウンロード中")

        self.assertTrue(self.window.open_output_button.isEnabled())

    def test_open_output_directory_reports_missing_directory(self) -> None:
        self.window.output_dir_input.setText("Z:/directory-that-does-not-exist")
        with patch.object(self.window, "_show_error") as show_error:
            self.window._open_output_dir()

        show_error.assert_called_once_with(
            "出力先エラー",
            "ダウンロード先ディレクトリが存在しません。",
        )


if __name__ == "__main__":
    unittest.main()
