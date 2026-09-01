"""CPU page."""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QMessageBox
from app.ui.widgets.cards import SectionHeader, Card
from app.power.power import list_plans, set_active


class CPUPage(QWidget):
    def __init__(self, hw, license_mgr):
        super().__init__()
        self.license_mgr = license_mgr
        root = QVBoxLayout(self); root.setContentsMargins(28,24,28,24); root.setSpacing(14)
        root.addWidget(SectionHeader("CPU", "Processor information and scheduling"))

        c = Card()
        c.layout().addWidget(QLabel(f"{hw.cpu.name}"))
        c.layout().addWidget(QLabel(
            f"Vendor: {hw.cpu.vendor}   Cores: {hw.cpu.cores}   Threads: {hw.cpu.threads}   "
            f"Clock: {hw.cpu.base_clock_mhz} MHz"
        ))
        root.addWidget(c)

        c2 = Card()
        c2.layout().addWidget(QLabel("POWER PLAN"))
        for p in list_plans():
            row = QHBoxLayout()
            row.addWidget(QLabel(f"  {p.name}{'  (active)' if p.active else ''}"))
            row.addStretch(1)
            if not p.active:
                b = QPushButton("Set Active")
                b.clicked.connect(lambda _=False, g=p.guid: (set_active(g),
                                    QMessageBox.information(self, "ZetaBoost", "Power plan applied.")))
                row.addWidget(b)
            c2.layout().addLayout(row)
        root.addWidget(c2)
        root.addStretch(1)
