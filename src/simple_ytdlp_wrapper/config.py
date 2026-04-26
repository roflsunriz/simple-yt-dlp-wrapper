from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


SOURCE_ROOT = Path(__file__).resolve().parents[2]
APP_DIR = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else SOURCE_ROOT
BUNDLE_DIR = Path(getattr(sys, "_MEIPASS", APP_DIR)) if getattr(sys, "frozen", False) else SOURCE_ROOT

# 設定ファイルパスを $env:USERPROFILE\mini-tools\simple-yt-dlp-wrapper\settings.json に変更
USERPROFILE = Path(os.environ.get("USERPROFILE", Path.home()))
CONFIG_DIR = USERPROFILE / "mini-tools" / "simple-yt-dlp-wrapper"
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_PATH = CONFIG_DIR / "settings.json"
LOG_DIR = CONFIG_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
WINDOWS_BIN_DIR = APP_DIR
RESOURCES_DIR = APP_DIR / "resources"
if not RESOURCES_DIR.exists():
    RESOURCES_DIR = BUNDLE_DIR / "resources"


@dataclass
class SettingsLoadResult:
    settings: "AppSettings"
    warning: str = ""


@dataclass
class AppSettings:
    download_mode: str = "best"
    video_format_id: str = ""
    audio_format_id: str = ""
    container: str = "mp4"
    audio_output_format: str = "mp3"
    audio_codec: str = "auto"
    audio_sample_rate: str = "auto"
    audio_bitrate: str = "auto"
    download_subtitle: bool = False
    embed_subtitle: bool = False
    output_dir: str = ""
    open_output_dir: bool = False
    file_name: str = ""

    @classmethod
    def defaults(cls) -> "AppSettings":
        return cls(output_dir=str(Path.home() / "Downloads"))

    @classmethod
    def load(cls) -> SettingsLoadResult:
        defaults = cls.defaults()
        
        # 古い設定ファイルから新しい場所に移行
        old_config_path = APP_DIR / "settings.json"
        if old_config_path.exists() and not CONFIG_PATH.exists():
            try:
                # 古い設定ファイルを新しい場所にコピー
                import shutil
                shutil.copy2(old_config_path, CONFIG_PATH)
                # 古いログディレクトリも移動（オプション）
                old_log_dir = APP_DIR / "logs"
                if old_log_dir.exists() and not LOG_DIR.exists():
                    shutil.copytree(old_log_dir, LOG_DIR, dirs_exist_ok=True)
            except Exception as exc:
                # 移行に失敗しても続行
                pass
        
        if not CONFIG_PATH.exists():
            cls.save(defaults)
            return SettingsLoadResult(settings=defaults)
        try:
            payload = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            merged = {**asdict(defaults), **payload}
            settings = cls(**merged)
        except Exception as exc:
            cls.save(defaults)
            return SettingsLoadResult(
                settings=defaults,
                warning=f"設定ファイルの読み込みに失敗したため既定値で復旧しました: {exc}",
            )

        if not Path(settings.output_dir).exists():
            settings.output_dir = defaults.output_dir
        return SettingsLoadResult(settings=settings)

    @staticmethod
    def save(settings: "AppSettings") -> None:
        CONFIG_PATH.write_text(
            json.dumps(asdict(settings), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
