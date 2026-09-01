"""Storage page."""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QMessageBox
from app.ui.widgets.cards import SectionHeader, Card
from app.storage.storage import optimize_drive


class StoragePage(QWidget):
    def __init__(self, hw, license_mgr):
        super().__init__()
        self.license_mgr = license_mgr
        root = QVBoxLayout(self); root.setContentsMargins(28,24,28,24); root.setSpacing(14)
        root.addWidget(SectionHeader("Storage", "TRIM for SSDs, defragment for HDDs, health overview"))

        for d in hw.disks:
            c = Card()
            c.layout().addWidget(QLabel(f"{d.mountpoint}   ({d.media_type})"))
            c.layout().addWidget(QLabel(
                f"{d.model or d.device}   •   {d.free_gb} GB free of {d.total_gb} GB   ({d.percent}% used)"
            ))
            row = QHBoxLayout()
            btn = QPushButton("Optimize"); btn.setObjectName("PrimaryButton")
            is_ssd = d.media_type.upper() in ("SSD", "NVME")
            btn.clicked.connect(lambda _=False, letter=d.mountpoint, ssd=is_ssd:
                                self._optimize(letter, ssd))
            row.addWidget(btn); row.addStretch(1)
            c.layout().addLayout(row)
            c.layout().addWidget(QLabel(
                "TRIM will be issued for SSD/NVMe drives; HDDs will be defragmented."
            ))
            root.addWidget(c)
        root.addStretch(1)

    def _optimize(self, letter, is_ssd):
        ok = optimize_drive(letter, is_ssd)
        QMessageBox.information(self, "ZetaBoost",
                                "Drive optimization started." if ok else "Failed or not available.")
