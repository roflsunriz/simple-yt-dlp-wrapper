from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


APP_DIR = Path(__file__).resolve().parents[2]
CONFIG_PATH = APP_DIR / "settings.json"
LOG_DIR = APP_DIR / "logs"
WINDOWS_BIN_DIR = APP_DIR


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
