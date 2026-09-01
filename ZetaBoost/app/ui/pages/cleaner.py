"""Cleaner page."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                                QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox, QMessageBox)
from app.ui.widgets.cards import SectionHeader, Card
from app.cleaner.cleaner import build_categories, scan_all
from app.core.constants import TIER_PRO


def _fmt(bytes_):
    if bytes_ <= 0: return "-"
    for u in ("B","KB","MB","GB"):
        if bytes_ < 1024: return f"{bytes_:.1f} {u}"
        bytes_ /= 1024
    return f"{bytes_:.1f} TB"


class CleanerPage(QWidget):
    def __init__(self, license_mgr):
        super().__init__()
        self.license_mgr = license_mgr
        self.categories = build_categories()
        self.scan_result = {}

        root = QVBoxLayout(self); root.setContentsMargins(28,24,28,24); root.setSpacing(14)
        root.addWidget(SectionHeader("Cleaner", "Free disk space by clearing safe caches and temporary files"))

        card = Card()
        h = QHBoxLayout()
        self.btn_scan = QPushButton("SCAN"); self.btn_scan.setObjectName("BoostButton")
        self.btn_clean = QPushButton("CLEAN SELECTED"); self.btn_clean.setObjectName("PrimaryButton")
        self.btn_clean.setEnabled(False)
        self.summary = QLabel("Click SCAN to estimate reclaimable space.")
        self.summary.setStyleSheet("color:#8b949e;")
        h.addWidget(self.btn_scan); h.addWidget(self.btn_clean); h.addStretch(1)
        card.layout().addLayout(h)
        card.layout().addWidget(self.summary)

        self.table = QTableWidget(len(self.categories), 4)
        self.table.setHorizontalHeaderLabels(["", "Category", "Size", "Tier"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        for i, c in enumerate(self.categories):
            chk = QCheckBox(); chk.setChecked(c.tier != TIER_PRO or license_mgr.is_pro())
            if c.tier == TIER_PRO and not license_mgr.is_pro(): chk.setEnabled(False)
            wrap = QWidget(); hl = QHBoxLayout(wrap); hl.setContentsMargins(8,0,0,0); hl.addWidget(chk); hl.addStretch(1)
            self.table.setCellWidget(i, 0, wrap)
            self.table.setItem(i, 1, QTableWidgetItem(c.name))
            self.table.setItem(i, 2, QTableWidgetItem("--"))
            self.table.setItem(i, 3, QTableWidgetItem(c.tier))
            self._store_checkbox(i, chk)
        card.layout().addWidget(self.table)
        root.addWidget(card)

        self.btn_scan.clicked.connect(self.on_scan)
        self.btn_clean.clicked.connect(self.on_clean)

    def _store_checkbox(self, row, chk):
        setattr(self, f"_chk_{row}", chk)

    def _get_checkbox(self, row):
        return getattr(self, f"_chk_{row}", None)

    def on_scan(self):
        self.scan_result = scan_all()
        total = 0
        for i, c in enumerate(self.categories):
            size = self.scan_result.get(c.id, 0)
            total += size
            self.table.item(i, 2).setText(_fmt(size))
        self.summary.setText(f"Potential space to free: {_fmt(total)}")
        self.btn_clean.setEnabled(True)

    def on_clean(self):
        freed = 0
        for i, c in enumerate(self.categories):
            chk = self._get_checkbox(i)
            if not chk or not chk.isChecked() or not chk.isEnabled(): continue
            if c.action:
                try: freed += c.action() or 0
                except Exception: pass
        QMessageBox.information(self, "ZetaBoost", f"Cleanup complete.\nFreed: {_fmt(freed)}")
        self.on_scan()
