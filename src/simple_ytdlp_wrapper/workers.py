from __future__ import annotations

from PyQt6.QtCore import QObject, QRunnable, pyqtSignal


class AnalysisSignals(QObject):
    finished = pyqtSignal(object)
    failed = pyqtSignal(str, str)


class DownloadSignals(QObject):
    progress = pyqtSignal(dict)
    finished = pyqtSignal()
    failed = pyqtSignal(str, str)
    cancelled = pyqtSignal()


class WorkerRunnable(QRunnable):
    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    def run(self) -> None:
        self.fn(*self.args, **self.kwargs)
