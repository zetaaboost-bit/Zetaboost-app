"""Windows Repair Center page."""
from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
                                QPlainTextEdit, QMessageBox)
from app.ui.widgets.cards import SectionHeader, Card
from app.repair.repair import (dism_check_health, dism_restore_health, sfc_scannow,
                                repair_windows_update)


class RepairWorker(QThread):
    line = Signal(str); done = Signal(bool, str)
    def __init__(self, fn): super().__init__(); self.fn = fn
    def run(self):
        r = self.fn(on_line=lambda l: self.line.emit(l))
        self.done.emit(r.ok, r.error)


class RepairPage(QWidget):
    def __init__(self, license_mgr):
        super().__init__()
        self.license_mgr = license_mgr
        self.worker = None
        root = QVBoxLayout(self); root.setContentsMargins(28,24,28,24); root.setSpacing(14)
        root.addWidget(SectionHeader("Repair Center", "DISM, SFC and Windows Update repair"))

        card = Card()
        row = QHBoxLayout()
        for label, fn in [("Quick: DISM /CheckHealth", dism_check_health),
                          ("Standard: DISM /RestoreHealth", dism_restore_health),
                          ("Standard: SFC /scannow", sfc_scannow),
                          ("Update: Reset WU", repair_windows_update)]:
            b = QPushButton(label)
            b.clicked.connect(lambda _=False, f=fn, l=label: self._start(f, l))
            row.addWidget(b)
        card.layout().addLayout(row)
        self.out = QPlainTextEdit(); self.out.setReadOnly(True); self.out.setMinimumHeight(340)
        card.layout().addWidget(self.out)
        root.addWidget(card, 1)

    def _start(self, fn, label):
        if self.worker and self.worker.isRunning():
            QMessageBox.information(self, "ZetaBoost", "A repair is already running."); return
        self.out.clear()
        self.out.appendPlainText(f"[{label}] starting...")
        self.worker = RepairWorker(fn)
        self.worker.line.connect(self.out.appendPlainText)
        self.worker.done.connect(lambda ok, err: self.out.appendPlainText(
            "Done." if ok else f"Failed: {err}"))
        self.worker.start()
