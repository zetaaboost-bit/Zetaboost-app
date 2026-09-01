"""Diagnostics page."""
import json
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                                QPlainTextEdit, QMessageBox)
from app.ui.widgets.cards import SectionHeader, Card
from app.diagnostics.diagnostics import generate_report


class DiagnosticsPage(QWidget):
    def __init__(self):
        super().__init__()
        root = QVBoxLayout(self); root.setContentsMargins(28,24,28,24); root.setSpacing(14)
        root.addWidget(SectionHeader("Diagnostics", "Generate a full ZetaBoost report"))

        card = Card()
        h = QHBoxLayout()
        btn = QPushButton("GENERATE REPORT"); btn.setObjectName("BoostButton")
        h.addWidget(btn); h.addStretch(1)
        card.layout().addLayout(h)
        self.text = QPlainTextEdit(); self.text.setReadOnly(True); self.text.setMinimumHeight(420)
        card.layout().addWidget(self.text)
        root.addWidget(card, 1)
        btn.clicked.connect(self._gen)

    def _gen(self):
        try:
            rep = generate_report()
            self.text.setPlainText(json.dumps(rep, indent=2))
            QMessageBox.information(self, "ZetaBoost", "Report saved to /logs.")
        except Exception as e:
            QMessageBox.warning(self, "ZetaBoost", f"Error: {e}")
