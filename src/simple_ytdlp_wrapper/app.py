import sys

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from .config import RESOURCES_DIR
from .logging_utils import configure_logging, log_event
from .main_window import MainWindow


def main() -> int:
    logger = configure_logging()

    def handle_exception(exc_type, exc_value, exc_traceback) -> None:
        log_event(
            logger,
            40,
            "unhandled_exception",
            code=getattr(exc_type, "__name__", "Exception"),
            detail=str(exc_value),
        )
        logger.exception("unhandled_exception", exc_info=(exc_type, exc_value, exc_traceback))

    sys.excepthook = handle_exception
    app = QApplication(sys.argv)
    app.setApplicationName("simple-yt-dlp-wrapper")
    icon_path = RESOURCES_DIR / "icon.ico"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    window = MainWindow()
    if icon_path.exists():
        window.setWindowIcon(QIcon(str(icon_path)))
    window.show()
    return app.exec()
