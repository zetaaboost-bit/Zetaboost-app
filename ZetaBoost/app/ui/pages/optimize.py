"""Optimization Center - individual tweaks by category."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                                QComboBox, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox)
from app.ui.widgets.cards import SectionHeader, Card
from app.optimization.tweak_database import all_tweaks, load_builtin_tweaks
from app.core.constants import TIER_PRO


class OptimizePage(QWidget):
    def __init__(self, engine, license_mgr):
        super().__init__()
        self.engine = engine
        self.license_mgr = license_mgr
        load_builtin_tweaks()

        root = QVBoxLayout(self); root.setContentsMargins(28,24,28,24); root.setSpacing(14)
        root.addWidget(SectionHeader("Optimization Center", "Fine-grained tweaks with apply and restore"))

        top = QHBoxLayout()
        self.combo = QComboBox()
        cats = sorted({t.category for t in all_tweaks()})
        self.combo.addItem("All Categories")
        for c in cats: self.combo.addItem(c)
        top.addWidget(QLabel("Category:"))
        top.addWidget(self.combo)
        top.addStretch(1)
        self.btn_refresh = QPushButton("Refresh")
        top.addWidget(self.btn_refresh)
        root.addLayout(top)

        card = Card()
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Name", "Category", "Risk", "Tier", "Status", "Actions"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        card.layout().addWidget(self.table)
        root.addWidget(card, 1)

        self.combo.currentIndexChanged.connect(self.reload)
        self.btn_refresh.clicked.connect(self.reload)
        self.reload()

    def reload(self):
        cat = self.combo.currentText()
        rows = [t for t in all_tweaks() if cat == "All Categories" or t.category == cat]
        self.table.setRowCount(len(rows))
        for i, t in enumerate(rows):
            self.table.setItem(i, 0, QTableWidgetItem(t.name))
            self.table.setItem(i, 1, QTableWidgetItem(t.category))
            self.table.setItem(i, 2, QTableWidgetItem(t.risk))
            tier_item = QTableWidgetItem(t.tier)
            self.table.setItem(i, 3, tier_item)
            self.table.setItem(i, 4, QTableWidgetItem(t.current_status()))
            wrap = QWidget()
            h = QHBoxLayout(wrap); h.setContentsMargins(4,2,4,2); h.setSpacing(6)
            apply_btn = QPushButton("Apply"); apply_btn.setObjectName("PrimaryButton")
            restore_btn = QPushButton("Restore")
            if t.tier == TIER_PRO and not self.license_mgr.is_pro():
                apply_btn.setEnabled(False); apply_btn.setText("PRO")
            apply_btn.clicked.connect(lambda _=False, tid=t.id: self._apply(tid))
            restore_btn.clicked.connect(lambda _=False, tid=t.id: self._restore(tid))
            h.addWidget(apply_btn); h.addWidget(restore_btn); h.addStretch(1)
            self.table.setCellWidget(i, 5, wrap)
        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)

    def _apply(self, tid):
        r = self.engine.apply_tweak(tid)
        QMessageBox.information(self, "ZetaBoost", r.message)
        self.reload()

    def _restore(self, tid):
        r = self.engine.restore_tweak(tid)
        QMessageBox.information(self, "ZetaBoost", r.message)
        self.reload()
