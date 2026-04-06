from __future__ import annotations

import os
import logging
import urllib.request
from pathlib import Path

from PyQt6.QtCore import QThreadPool, Qt
from PyQt6.QtGui import QCloseEvent, QGuiApplication, QPixmap
from PyQt6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .config import AppSettings
from .dependencies import DependencyStatus, detect_dependencies
from .filename_utils import sanitize_file_basename
from .logging_utils import configure_logging, log_event
from .models import AnalysisResult, DownloadContext, FormatOption, StateConfig
from .workers import AnalysisSignals, DownloadSignals, WorkerRunnable
from .yt_dlp_service import (
    DownloadCancelledError,
    YtDlpError,
    analyze_url,
    build_download_command,
    cleanup_cancelled_download,
    describe_mode_selection,
    format_bytes,
    run_download,
    select_1080p_video,
    snapshot_existing_paths,
)

STATE_CONFIGS = {
    "初期": StateConfig(True, True, False, False, True, True, True),
    "分析中": StateConfig(False, False, False, False, False, False, False),
    "分析成功": StateConfig(True, True, True, False, True, True, True),
    "分析失敗": StateConfig(True, True, False, False, True, True, True),
    "ダウンロード中": StateConfig(False, False, False, True, False, False, False),
    "完了": StateConfig(True, True, False, False, True, True, True),
    "中止": StateConfig(True, True, False, False, True, True, True),
    "エラー": StateConfig(True, True, False, False, True, True, True),
}


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("simple-yt-dlp-wrapper")
        self.resize(1100, 760)

        self.logger = configure_logging()
        self.thread_pool = QThreadPool.globalInstance()
        settings_result = AppSettings.load()
        self.settings = settings_result.settings
        self.settings_load_warning = settings_result.warning
        self.dependencies: DependencyStatus = detect_dependencies()
        self.analysis_result: AnalysisResult | None = None
        self.download_context: DownloadContext | None = None
        self.cancel_requested = False
        self.status_name = "初期"

        self._build_ui()
        self._apply_settings()
        self._show_dependency_warnings()
        self._set_state("初期")

    def _build_ui(self) -> None:
        central = QWidget(self)
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        url_row = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("動画 URL を入力")
        self.paste_button = QPushButton("ペースト")
        self.analyze_button = QPushButton("URL分析")
        self.paste_button.clicked.connect(self._paste_url)
        self.analyze_button.clicked.connect(self._start_analysis)
        url_row.addWidget(self.url_input)
        url_row.addWidget(self.paste_button)
        url_row.addWidget(self.analyze_button)
        root.addLayout(url_row)

        info_layout = QGridLayout()
        self.title_value = QLineEdit()
        self.title_value.setReadOnly(True)
        self.description_value = QTextEdit()
        self.description_value.setReadOnly(True)
        self.thumbnail_label = QLabel("サムネイル")
        self.thumbnail_label.setFixedSize(320, 180)
        self.thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumbnail_label.setStyleSheet("border: 1px solid #999;")
        info_layout.addWidget(QLabel("タイトル"), 0, 0)
        info_layout.addWidget(self.title_value, 0, 1)
        info_layout.addWidget(QLabel("説明"), 1, 0)
        info_layout.addWidget(self.description_value, 1, 1)
        info_layout.addWidget(self.thumbnail_label, 0, 2, 2, 1)
        root.addLayout(info_layout)

        mode_group = QGroupBox("ダウンロードモード")
        mode_layout = QVBoxLayout(mode_group)
        self.best_radio = QRadioButton("最高画質モード")
        self.fullhd_radio = QRadioButton("1080pモード")
        self.manual_radio = QRadioButton("マニュアルモード")
        self.mode_buttons = QButtonGroup(self)
        for button in (self.best_radio, self.fullhd_radio, self.manual_radio):
            self.mode_buttons.addButton(button)
            button.toggled.connect(self._update_manual_controls)
            mode_layout.addWidget(button)
        root.addWidget(mode_group)

        manual_group = QGroupBox("マニュアル選択")
        manual_layout = QGridLayout(manual_group)
        self.video_combo = QComboBox()
        self.audio_combo = QComboBox()
        self.container_combo = QComboBox()
        self.container_combo.addItems(["mp4", "mkv"])
        self.video_combo.currentIndexChanged.connect(self._sync_manual_selection_state)
        self.audio_combo.currentIndexChanged.connect(self._update_mode_summary)
        manual_layout.addWidget(QLabel("画質"), 0, 0)
        manual_layout.addWidget(self.video_combo, 0, 1)
        manual_layout.addWidget(QLabel("音質"), 1, 0)
        manual_layout.addWidget(self.audio_combo, 1, 1)
        manual_layout.addWidget(QLabel("出力コンテナ"), 2, 0)
        manual_layout.addWidget(self.container_combo, 2, 1)
        root.addWidget(manual_group)

        options_row = QHBoxLayout()
        self.subtitle_checkbox = QCheckBox("字幕をダウンロード")
        self.embed_subtitle_checkbox = QCheckBox("字幕を埋め込む")
        self.open_output_checkbox = QCheckBox("完了後に出力先を開く")
        self.subtitle_checkbox.toggled.connect(self._handle_subtitle_toggle)
        self.embed_subtitle_checkbox.toggled.connect(self._update_subtitle_summary)
        options_row.addWidget(self.subtitle_checkbox)
        options_row.addWidget(self.embed_subtitle_checkbox)
        options_row.addWidget(self.open_output_checkbox)
        root.addLayout(options_row)

        subtitle_row = QHBoxLayout()
        self.subtitle_summary_label = QLabel("字幕候補: なし")
        subtitle_row.addWidget(self.subtitle_summary_label)
        subtitle_row.addStretch(1)
        root.addLayout(subtitle_row)

        self.mode_summary_label = QLabel("既定候補: -")
        root.addWidget(self.mode_summary_label)

        output_row = QHBoxLayout()
        self.output_dir_input = QLineEdit()
        self.browse_output_button = QPushButton("出力先選択")
        self.default_output_button = QPushButton("デフォルト")
        self.browse_output_button.clicked.connect(self._browse_output_dir)
        self.default_output_button.clicked.connect(self._set_default_output_dir)
        output_row.addWidget(QLabel("ダウンロード先"))
        output_row.addWidget(self.output_dir_input)
        output_row.addWidget(self.browse_output_button)
        output_row.addWidget(self.default_output_button)
        root.addLayout(output_row)

        filename_row = QHBoxLayout()
        self.filename_input = QLineEdit()
        filename_row.addWidget(QLabel("ファイル名"))
        filename_row.addWidget(self.filename_input)
        root.addLayout(filename_row)

        action_row = QHBoxLayout()
        self.save_settings_button = QPushButton("設定保存")
        self.open_log_button = QPushButton("ログを開く")
        self.download_button = QPushButton("ダウンロード開始")
        self.cancel_button = QPushButton("中止")
        self.save_settings_button.clicked.connect(self._save_settings)
        self.open_log_button.clicked.connect(self._open_latest_log)
        self.download_button.clicked.connect(self._start_download)
        self.cancel_button.clicked.connect(self._cancel_download)
        action_row.addWidget(self.save_settings_button)
        action_row.addWidget(self.open_log_button)
        action_row.addStretch(1)
        action_row.addWidget(self.download_button)
        action_row.addWidget(self.cancel_button)
        root.addLayout(action_row)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        root.addWidget(self.progress_bar)

        self.status_label = QLabel("状態: 初期")
        root.addWidget(self.status_label)

        self.status_details = QPlainTextEdit()
        self.status_details.setReadOnly(True)
        root.addWidget(self.status_details)

    def _apply_settings(self) -> None:
        self.output_dir_input.setText(self.settings.output_dir)
        self.filename_input.setText(self.settings.file_name)
        self.subtitle_checkbox.setChecked(self.settings.download_subtitle)
        self.embed_subtitle_checkbox.setChecked(self.settings.embed_subtitle)
        self.open_output_checkbox.setChecked(self.settings.open_output_dir)
        self.container_combo.setCurrentText(self.settings.container)
        self.embed_subtitle_checkbox.setEnabled(False)
        if self.settings.download_mode == "manual":
            self.manual_radio.setChecked(True)
        elif self.settings.download_mode == "1080p":
            self.fullhd_radio.setChecked(True)
        else:
            self.best_radio.setChecked(True)
        self._update_manual_controls()

    def _show_dependency_warnings(self) -> None:
        messages = []
        if self.settings_load_warning:
            log_event(
                self.logger,
                logging.WARNING,
                "settings_load_recovered",
                code="settings_load_failed",
                detail=self.settings_load_warning,
            )
            messages.append(self.settings_load_warning)
        if not self.dependencies.has_yt_dlp:
            log_event(self.logger, logging.WARNING, "dependency_missing", code="missing_yt_dlp")
            messages.append("yt-dlp が見つかりません。URL分析とダウンロードは利用できません。")
        if not self.dependencies.has_ffmpeg:
            log_event(self.logger, logging.WARNING, "dependency_missing", code="missing_ffmpeg")
            messages.append("ffmpeg が見つかりません。マージが必要なダウンロードは利用できません。")
        if messages:
            QMessageBox.warning(self, "依存関係の警告", "\n".join(messages))

    def _set_state(self, state: str) -> None:
        self.status_name = state
        self.status_label.setText(f"状態: {state}")
        config = STATE_CONFIGS[state]
        self.url_input.setEnabled(config.url_input)
        self.paste_button.setEnabled(config.url_input)
        self.analyze_button.setEnabled(config.analyze and self.dependencies.has_yt_dlp)
        self.cancel_button.setEnabled(config.cancel)
        self.save_settings_button.setEnabled(config.settings)
        self.open_log_button.setEnabled(True)
        self.output_dir_input.setEnabled(config.output_controls)
        self.filename_input.setEnabled(config.output_controls)
        self.browse_output_button.setEnabled(config.output_controls)
        self.default_output_button.setEnabled(config.output_controls)
        self.best_radio.setEnabled(config.mode_controls)
        self.fullhd_radio.setEnabled(config.mode_controls)
        self.manual_radio.setEnabled(config.mode_controls)
        self.subtitle_checkbox.setEnabled(config.mode_controls and bool(self.analysis_result and self.analysis_result.subtitles))
        self.embed_subtitle_checkbox.setEnabled(
            config.mode_controls and self.subtitle_checkbox.isChecked() and bool(self.analysis_result and self.analysis_result.subtitles)
        )
        self.download_button.setEnabled(config.download and self._download_ready())
        self._update_manual_controls()

    def _download_ready(self) -> bool:
        if not self.analysis_result or not self.dependencies.has_yt_dlp:
            return False
        output_text = self.output_dir_input.text().strip()
        if not output_text:
            return False
        if not Path(output_text).exists():
            return False
        if self.manual_radio.isChecked():
            selected_video = self._selected_video_option()
            if not selected_video:
                return False
            if selected_video.kind == "映像専用":
                return bool(self.audio_combo.currentData())
        return True

    def _update_manual_controls(self) -> None:
        enabled = self.manual_radio.isChecked() and self.status_name != "ダウンロード中"
        self.video_combo.setEnabled(enabled)
        self._sync_manual_selection_state()
        if self.status_name == "分析成功":
            self.download_button.setEnabled(self._download_ready())
        self._update_mode_summary()

    def _paste_url(self) -> None:
        self.url_input.setText(QGuiApplication.clipboard().text().strip())

    def _start_analysis(self) -> None:
        url = self.url_input.text().strip()
        if not url:
            self._show_error("URL 未入力", "URL を入力してください。")
            return
        log_event(self.logger, logging.INFO, "analysis_started", url=url)
        self._set_state("分析中")
        self.status_details.setPlainText("分析中...")
        signals = AnalysisSignals()
        signals.finished.connect(self._handle_analysis_success)
        signals.failed.connect(self._handle_analysis_failure)
        self.thread_pool.start(WorkerRunnable(self._run_analysis, url, signals))

    def _run_analysis(self, url: str, signals: AnalysisSignals) -> None:
        try:
            signals.finished.emit(analyze_url(url, self.dependencies))
        except YtDlpError as exc:
            log_event(self.logger, logging.WARNING, "analysis_failed", url=url, code=exc.code, detail=exc.details)
            signals.failed.emit(exc.summary, exc.details)
        except Exception as exc:
            log_event(self.logger, logging.ERROR, "analysis_failed", url=url, code="unexpected_error", detail=str(exc))
            self.logger.exception("analysis_failed url=%s", url)
            signals.failed.emit("URL分析失敗", str(exc))

    def _handle_analysis_success(self, result: AnalysisResult) -> None:
        self.analysis_result = result
        log_event(
            self.logger,
            logging.INFO,
            "analysis_succeeded",
            url=result.original_url,
            detail=f"video_formats={len(result.video_formats)} audio_formats={len(result.audio_formats)} subtitles={len(result.subtitles)}",
        )
        self.title_value.setText(result.title)
        self.description_value.setPlainText(result.description)
        self.filename_input.setText(sanitize_file_basename(result.title))
        self._load_thumbnail(result.thumbnail_url)
        self._populate_format_combos(result)
        self._apply_mode_defaults()
        if not result.subtitles:
            self.subtitle_checkbox.setChecked(False)
            self.embed_subtitle_checkbox.setChecked(False)
        self._update_subtitle_summary()
        self.status_details.setPlainText(
            "\n".join(
                [
                    "分析成功",
                    f"判定: 実用的なダウンロード候補あり ({'動画' if result.video_formats else '音声'}取得可)",
                    f"動画候補: {len(result.video_formats)}",
                    f"音声候補: {len(result.audio_formats)}",
                    f"字幕候補: {len(result.subtitles)}",
                ]
            )
        )
        self._set_state("分析成功")

    def _handle_analysis_failure(self, summary: str, details: str) -> None:
        self.analysis_result = None
        self._set_state("分析失敗")
        self._show_error(summary, details, detailed_title="分析詳細")

    def _populate_format_combos(self, result: AnalysisResult) -> None:
        self.video_combo.clear()
        self.audio_combo.clear()
        for item in self._manual_video_candidates(result):
            self.video_combo.addItem(item.label, item.format_id)
        for item in result.audio_formats:
            self.audio_combo.addItem(item.label, item.format_id)
        video_index = self.video_combo.findData(self.settings.video_format_id)
        if video_index >= 0:
            self.video_combo.setCurrentIndex(video_index)
        audio_index = self.audio_combo.findData(self.settings.audio_format_id)
        if audio_index >= 0:
            self.audio_combo.setCurrentIndex(audio_index)
        self._sync_manual_selection_state()
        self._update_subtitle_summary()
        self._update_mode_summary()

    def _load_thumbnail(self, url: str) -> None:
        self.thumbnail_label.setPixmap(QPixmap())
        if not url:
            self.thumbnail_label.setText("サムネイルなし")
            return
        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                image_data = response.read()
        except Exception:
            self.thumbnail_label.setText("サムネイル取得失敗")
            return
        pixmap = QPixmap()
        if not pixmap.loadFromData(image_data):
            self.thumbnail_label.setText("サムネイル表示失敗")
            return
        self.thumbnail_label.setText("")
        self.thumbnail_label.setPixmap(
            pixmap.scaled(
                self.thumbnail_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

    def _browse_output_dir(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "出力先を選択", self.output_dir_input.text())
        if directory:
            self.output_dir_input.setText(directory)
            if self.status_name == "分析成功":
                self.download_button.setEnabled(self._download_ready())

    def _set_default_output_dir(self) -> None:
        self.output_dir_input.setText(str(Path.home() / "Downloads"))
        if self.status_name == "分析成功":
            self.download_button.setEnabled(self._download_ready())

    def _start_download(self) -> None:
        if not self.analysis_result:
            self._show_error("分析未完了", "URL分析を先に実行してください。")
            return
        output_text = self.output_dir_input.text().strip()
        if not output_text:
            self._show_error("出力先未指定", "ダウンロード先ディレクトリを指定してください。")
            return
        output_dir = Path(output_text)
        if not output_dir.exists():
            self._show_error("出力先エラー", "ダウンロード先ディレクトリが存在しません。")
            return

        basename = sanitize_file_basename(self.filename_input.text().strip() or self.analysis_result.title)
        overwrite = False
        if self._output_exists(output_dir, basename):
            reply = QMessageBox.question(
                self,
                "ファイル衝突",
                "同名ファイルが既に存在します。上書きしますか。",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Cancel,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
            overwrite = True

        mode = "manual" if self.manual_radio.isChecked() else "1080p" if self.fullhd_radio.isChecked() else "best"
        try:
            command = build_download_command(
                dependencies=self.dependencies,
                analysis=self.analysis_result,
                output_dir=str(output_dir),
                file_basename=basename,
                mode=mode,
                video_format_id=self.video_combo.currentData() or "",
                audio_format_id=self.audio_combo.currentData() or "",
                container=self.container_combo.currentText(),
                download_subtitle=self.subtitle_checkbox.isChecked(),
                embed_subtitle=self.embed_subtitle_checkbox.isChecked(),
                overwrite=overwrite,
            )
        except YtDlpError as exc:
            log_event(
                self.logger,
                logging.WARNING,
                "download_precheck_failed",
                url=self.analysis_result.original_url,
                code=exc.code,
                detail=exc.details,
            )
            self._show_error(exc.summary, exc.details)
            return

        self.cancel_requested = False
        self.download_context = DownloadContext(
            output_dir=output_dir,
            basename=basename,
            existing_paths=snapshot_existing_paths(output_dir, basename),
        )
        log_event(
            self.logger,
            logging.INFO,
            "download_started",
            url=self.analysis_result.original_url,
            detail=f"mode={mode} output_dir={output_dir} basename={basename}",
        )
        self.progress_bar.setValue(0)
        self.status_details.setPlainText("ダウンロード開始")
        self._set_state("ダウンロード中")

        signals = DownloadSignals()
        signals.progress.connect(self._handle_download_progress)
        signals.finished.connect(self._handle_download_success)
        signals.failed.connect(self._handle_download_failure)
        signals.cancelled.connect(self._handle_download_cancelled)
        self.thread_pool.start(WorkerRunnable(self._run_download, command, signals))

    def _run_download(self, command: list[str], signals: DownloadSignals) -> None:
        try:
            run_download(
                command,
                self.dependencies,
                on_progress=signals.progress.emit,
                is_cancelled=lambda: self.cancel_requested,
                on_output_path=lambda _path: None,
            )
        except DownloadCancelledError:
            log_event(
                self.logger,
                logging.INFO,
                "download_cancelled",
                url=self.analysis_result.original_url if self.analysis_result else "",
                code="download_cancelled",
            )
            signals.cancelled.emit()
            return
        except YtDlpError as exc:
            if self.cancel_requested:
                signals.cancelled.emit()
                return
            log_event(
                self.logger,
                logging.WARNING,
                "download_failed",
                url=self.analysis_result.original_url if self.analysis_result else "",
                code=exc.code,
                detail=exc.details,
            )
            signals.failed.emit(exc.summary, exc.details)
            return
        except Exception as exc:
            if self.cancel_requested:
                signals.cancelled.emit()
                return
            log_event(
                self.logger,
                logging.ERROR,
                "download_failed",
                url=self.analysis_result.original_url if self.analysis_result else "",
                code="unexpected_error",
                detail=str(exc),
            )
            self.logger.exception("download_failed url=%s", self.analysis_result.original_url if self.analysis_result else "")
            signals.failed.emit("ダウンロード失敗", str(exc))
            return
        if self.cancel_requested:
            signals.cancelled.emit()
        else:
            signals.finished.emit()

    def _handle_download_progress(self, payload: dict) -> None:
        percent = payload.get("percent")
        if percent is not None:
            self.progress_bar.setValue(int(percent))
        self.status_details.setPlainText(
            "\n".join(
                [
                    payload.get("step", ""),
                    f"速度: {payload.get('speed', '-')}",
                    f"ETA: {payload.get('eta', '-')}",
                    f"ダウンロード済み: {format_bytes(payload.get('downloaded_bytes'))}",
                    f"残り: {format_bytes(payload.get('remaining_bytes'))}",
                    payload.get("raw", ""),
                ]
            ).strip()
        )

    def _handle_download_success(self) -> None:
        log_event(
            self.logger,
            logging.INFO,
            "download_succeeded",
            url=self.analysis_result.original_url if self.analysis_result else "",
        )
        self.download_context = None
        self.progress_bar.setValue(100)
        self._set_state("完了")
        self.status_details.setPlainText("ダウンロード完了")
        if self.open_output_checkbox.isChecked():
            self._open_output_dir()

    def _handle_download_failure(self, summary: str, details: str) -> None:
        self._set_state("エラー")
        self._show_error(summary, details, detailed_title="ダウンロード詳細")

    def _handle_download_cancelled(self) -> None:
        removed = cleanup_cancelled_download(self.download_context) if self.download_context else []
        log_event(
            self.logger,
            logging.INFO,
            "download_cancelled_cleanup",
            url=self.analysis_result.original_url if self.analysis_result else "",
            detail=f"removed={','.join(path.name for path in removed)}" if removed else "removed=none",
        )
        self.download_context = None
        self._set_state("中止")
        details = ["ダウンロードを中止しました。"]
        if removed:
            details.append("削除した未完成ファイル:")
            details.extend(path.name for path in removed)
        self.status_details.setPlainText("\n".join(details))

    def _cancel_download(self) -> None:
        self.cancel_requested = True
        self.status_details.appendPlainText("中止要求を送信しました。")

    def _open_output_dir(self) -> None:
        output_dir = self.output_dir_input.text().strip()
        if output_dir and Path(output_dir).exists():
            os.startfile(output_dir)

    def _output_exists(self, output_dir: Path, basename: str) -> bool:
        return any(candidate.is_file() for candidate in output_dir.glob(f"{basename}.*"))

    def _save_settings(self) -> None:
        self._collect_settings()
        try:
            AppSettings.save(self.settings)
        except Exception as exc:
            log_event(self.logger, logging.ERROR, "settings_save_failed", code="settings_save_failed", detail=str(exc))
            self.logger.exception("settings_save_failed")
            self._show_error("設定保存失敗", str(exc))
            return
        log_event(self.logger, logging.INFO, "settings_saved")
        self.status_details.appendPlainText("設定を保存しました。")

    def _collect_settings(self) -> None:
        self.settings.download_mode = (
            "manual" if self.manual_radio.isChecked() else "1080p" if self.fullhd_radio.isChecked() else "best"
        )
        self.settings.video_format_id = self.video_combo.currentData() or ""
        self.settings.audio_format_id = self.audio_combo.currentData() or ""
        self.settings.container = self.container_combo.currentText()
        self.settings.download_subtitle = self.subtitle_checkbox.isChecked()
        self.settings.embed_subtitle = self.embed_subtitle_checkbox.isChecked()
        self.settings.output_dir = self.output_dir_input.text().strip()
        self.settings.open_output_dir = self.open_output_checkbox.isChecked()
        self.settings.file_name = self.filename_input.text().strip()

    def _show_error(self, summary: str, details: str, detailed_title: str = "詳細") -> None:
        self.status_details.setPlainText(f"{summary}\n[{detailed_title}]\n{details}")
        QMessageBox.critical(self, summary, details)

    def _manual_video_candidates(self, result: AnalysisResult) -> list[FormatOption]:
        if self.dependencies.has_ffmpeg:
            return result.video_formats
        return [item for item in result.video_formats if item.kind != "映像専用"]

    def _selected_video_option(self) -> FormatOption | None:
        if not self.analysis_result:
            return None
        format_id = self.video_combo.currentData()
        return next((item for item in self.analysis_result.video_formats if item.format_id == format_id), None)

    def _sync_manual_selection_state(self) -> None:
        manual_enabled = self.manual_radio.isChecked() and self.status_name != "ダウンロード中"
        selected_video = self._selected_video_option()
        needs_audio = bool(selected_video and selected_video.kind == "映像専用")
        self.audio_combo.setEnabled(manual_enabled and needs_audio)
        self.container_combo.setEnabled(manual_enabled and needs_audio)
        if manual_enabled and selected_video and not needs_audio:
            self.audio_combo.setCurrentIndex(-1)
        if self.status_name == "分析成功":
            self.download_button.setEnabled(self._download_ready())
        self._update_mode_summary()

    def _update_mode_summary(self) -> None:
        if not self.analysis_result:
            self.mode_summary_label.setText("既定候補: -")
            return
        if self.manual_radio.isChecked():
            video = self.video_combo.currentText() or "-"
            audio = self.audio_combo.currentText() if self.audio_combo.isEnabled() else "不要"
            self.mode_summary_label.setText(f"既定候補: 動画={video} / 音声={audio}")
            return
        if self.fullhd_radio.isChecked():
            self.mode_summary_label.setText(
                f"既定候補: {describe_mode_selection('1080p', self.analysis_result)}"
            )
            return
        self.mode_summary_label.setText(
            f"既定候補: {describe_mode_selection('best', self.analysis_result)}"
        )

    def _update_subtitle_summary(self) -> None:
        if not self.analysis_result or not self.analysis_result.subtitles:
            self.subtitle_summary_label.setText("字幕候補: なし")
            return
        parts = []
        for item in self.analysis_result.subtitles[:5]:
            label = f"{item.language} ({item.ext}{', 自動生成' if item.auto_generated else ''})"
            parts.append(label)
        prefix = "選択予定" if self.subtitle_checkbox.isChecked() else "字幕候補"
        summary = " / ".join(parts)
        if len(self.analysis_result.subtitles) > 5:
            summary += " / ..."
        self.subtitle_summary_label.setText(f"{prefix}: {summary}")

    def _handle_subtitle_toggle(self, checked: bool) -> None:
        self.embed_subtitle_checkbox.setEnabled(
            checked and self.status_name != "ダウンロード中" and bool(self.analysis_result and self.analysis_result.subtitles)
        )
        if not checked:
            self.embed_subtitle_checkbox.setChecked(False)
        self._update_subtitle_summary()

    def _apply_mode_defaults(self) -> None:
        if not self.analysis_result:
            return
        if self.best_radio.isChecked():
            self.video_combo.setCurrentIndex(0)
            self.audio_combo.setCurrentIndex(0 if self.audio_combo.count() else -1)
        elif self.fullhd_radio.isChecked():
            default_video = select_1080p_video(self._manual_video_candidates(self.analysis_result))
            index = self.video_combo.findData(default_video.format_id) if default_video else -1
            self.video_combo.setCurrentIndex(index if index >= 0 else (0 if self.video_combo.count() else -1))
            self.audio_combo.setCurrentIndex(0 if self.audio_combo.count() else -1)
        else:
            if self.video_combo.currentIndex() < 0 and self.video_combo.count():
                self.video_combo.setCurrentIndex(0)
            if self.audio_combo.currentIndex() < 0 and self.audio_combo.count():
                self.audio_combo.setCurrentIndex(0)
        self._sync_manual_selection_state()
        self._update_mode_summary()

    def _open_latest_log(self) -> None:
        log_dir = Path(__file__).resolve().parents[2] / "logs"
        if not log_dir.exists():
            self._show_error("ログ未作成", "ログファイルはまだ作成されていません。")
            return
        candidates = sorted(log_dir.glob("*.log"), key=lambda path: path.stat().st_mtime, reverse=True)
        if not candidates:
            self._show_error("ログ未作成", "ログファイルはまだ作成されていません。")
            return
        os.startfile(candidates[0])

    def closeEvent(self, event: QCloseEvent) -> None:
        self._collect_settings()
        try:
            AppSettings.save(self.settings)
            log_event(self.logger, logging.INFO, "settings_saved_on_exit")
        except Exception:
            log_event(self.logger, logging.ERROR, "settings_save_failed_on_exit", code="settings_save_failed")
            self.logger.exception("settings_save_failed_on_exit")
        super().closeEvent(event)
