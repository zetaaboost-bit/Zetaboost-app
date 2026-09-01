"""GPU page."""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QMessageBox, QHBoxLayout
from app.ui.widgets.cards import SectionHeader, Card
from app.optimization.tweak_database import get_tweak


class GPUPage(QWidget):
    def __init__(self, hw, license_mgr):
        super().__init__()
        self.license_mgr = license_mgr
        root = QVBoxLayout(self); root.setContentsMargins(28,24,28,24); root.setSpacing(14)
        root.addWidget(SectionHeader("GPU", "Vendor-aware graphics optimizations"))

        for g in hw.gpus:
            c = Card()
            c.layout().addWidget(QLabel(f"{g.name}"))
            c.layout().addWidget(QLabel(f"Vendor: {g.vendor}    VRAM: {g.vram_mb} MB    Driver: {g.driver_version or '-'}"))
            root.addWidget(c)

        # HAGS tweak
        c = Card()
        c.layout().addWidget(QLabel("HARDWARE-ACCELERATED GPU SCHEDULING (HAGS) [PRO]"))
        t = get_tweak("gpu.hags_on")
        status = t.current_status() if t else "unknown"
        c.layout().addWidget(QLabel(f"Current: {status}"))
        h = QHBoxLayout()
        btn = QPushButton("Enable HAGS"); btn.setObjectName("PrimaryButton")
        if not license_mgr.is_pro():
            btn.setEnabled(False); btn.setText("Enable HAGS  [PRO]")
        btn.clicked.connect(lambda: self._apply(t))
        h.addWidget(btn); h.addStretch(1)
        c.layout().addLayout(h)
        c.layout().addWidget(QLabel("Requires reboot to take effect. May improve latency on modern GPUs."))
        root.addWidget(c)

        c2 = Card()
        c2.layout().addWidget(QLabel("VENDOR-SPECIFIC PANELS"))
        c2.layout().addWidget(QLabel("Full vendor SDK integration (NVML, ADL) - NOT IMPLEMENTED YET."))
        root.addWidget(c2)
        root.addStretch(1)

    def _apply(self, t):
        if not t: return
        r = t.apply()
        QMessageBox.information(self, "ZetaBoost", "HAGS enabled. Reboot required." if r.ok else r.error)
