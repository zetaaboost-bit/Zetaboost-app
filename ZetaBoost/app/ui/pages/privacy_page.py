"""Privacy Center page."""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
                                QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox)
from app.ui.widgets.cards import SectionHeader, Card
from app.privacy.privacy import list_privacy_tweaks


class PrivacyPage(QWidget):
    def __init__(self, engine, license_mgr):
        super().__init__()
        self.engine = engine
        self.license_mgr = license_mgr
        root = QVBoxLayout(self); root.setContentsMargins(28,24,28,24); root.setSpacing(14)
        root.addWidget(SectionHeader("Privacy Center", "Reversible telemetry & data collection controls"))

        card = Card()
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Setting", "Current", "Description", "Actions"])
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        card.layout().addWidget(self.table)
        root.addWidget(card, 1)
        self.reload()

    def reload(self):
        tweaks = list_privacy_tweaks()
        self.table.setRowCount(len(tweaks))
        for i, t in enumerate(tweaks):
            self.table.setItem(i, 0, QTableWidgetItem(t.name))
            self.table.setItem(i, 1, QTableWidgetItem(t.current_status()))
            self.table.setItem(i, 2, QTableWidgetItem(t.description))
            wrap = QWidget(); h = QHBoxLayout(wrap); h.setContentsMargins(2,2,2,2)
            b1 = QPushButton("Apply"); b1.setObjectName("PrimaryButton")
            b2 = QPushButton("Restore")
            b1.clicked.connect(lambda _=False, tid=t.id: self._apply(tid))
            b2.clicked.connect(lambda _=False, tid=t.id: self._restore(tid))
            h.addWidget(b1); h.addWidget(b2)
            self.table.setCellWidget(i, 3, wrap)

    def _apply(self, tid):
        r = self.engine.apply_tweak(tid); QMessageBox.information(self, "ZetaBoost", r.message); self.reload()
    def _restore(self, tid):
        r = self.engine.restore_tweak(tid); QMessageBox.information(self, "ZetaBoost", r.message); self.reload()
