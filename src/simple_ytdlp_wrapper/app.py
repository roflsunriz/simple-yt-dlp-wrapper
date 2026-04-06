import sys

from PyQt6.QtWidgets import QApplication

from .main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("simple-yt-dlp-wrapper")
    window = MainWindow()
    window.show()
    return app.exec()
