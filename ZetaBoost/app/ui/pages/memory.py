"""Memory / RAM page."""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QMessageBox
from app.ui.widgets.cards import SectionHeader, Card, MetricBar
from app.memory.memory import get_memory_report, trim_working_sets


class MemoryPage(QWidget):
    def __init__(self, monitor):
        super().__init__()
        root = QVBoxLayout(self); root.setContentsMargins(28,24,28,24); root.setSpacing(14)
        root.addWidget(SectionHeader("Memory", "RAM usage, commit, and safe cleanup"))

        rep = get_memory_report()
        card = Card()
        card.layout().addWidget(QLabel(
            f"Total: {rep.total_gb} GB   •   Used: {rep.used_gb} GB ({rep.percent}%)   •   Available: {rep.available_gb} GB"
        ))
        card.layout().addWidget(QLabel(
            f"Commit: {rep.commit_used_gb} / {rep.commit_total_gb} GB   •   Pagefile: {rep.swap_used_gb} / {rep.swap_total_gb} GB"
        ))
        root.addWidget(card)

        bar = MetricBar("RAM")
        bar.set_percent(rep.percent, f"{rep.used_gb} / {rep.total_gb} GB")
        monitor.updated.connect(lambda s: bar.set_percent(s.ram_percent, f"{s.ram_used_gb} / {s.ram_total_gb} GB"))
        root.addWidget(bar)

        c = Card()
        c.layout().addWidget(QLabel("SAFE ACTIONS"))
        h = QHBoxLayout()
        b1 = QPushButton("Trim Working Sets"); b1.setObjectName("PrimaryButton")
        b1.clicked.connect(self._trim)
        h.addWidget(b1); h.addStretch(1)
        c.layout().addLayout(h)
        c.layout().addWidget(QLabel(
            "ZetaBoost does not use fake RAM boosters. Trim asks Windows to release cached working sets."
        ))
        root.addWidget(c)
        root.addStretch(1)

    def _trim(self):
        ok = trim_working_sets()
        QMessageBox.information(self, "ZetaBoost", "Working sets trimmed." if ok else "Not available.")
