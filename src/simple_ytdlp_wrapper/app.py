import sys

from PyQt6.QtWidgets import QApplication

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
    window = MainWindow()
    window.show()
    return app.exec()
