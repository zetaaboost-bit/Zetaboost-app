"""Services page."""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                                QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QMessageBox)
from app.ui.widgets.cards import SectionHeader, Card
from app.services.services_manager import list_services, set_startup, CATEGORIES


class ServicesPage(QWidget):
    def __init__(self, license_mgr):
        super().__init__()
        self.license_mgr = license_mgr
        root = QVBoxLayout(self); root.setContentsMargins(28,24,28,24); root.setSpacing(14)
        root.addWidget(SectionHeader("Services", "Manage Windows services safely"))

        row = QHBoxLayout()
        row.addWidget(QLabel("Category:"))
        self.combo = QComboBox()
        self.combo.addItem("All")
        for c in CATEGORIES.keys(): self.combo.addItem(c)
        row.addWidget(self.combo)
        row.addStretch(1)
        self.btn_reload = QPushButton("Reload")
        row.addWidget(self.btn_reload)
        root.addLayout(row)

        card = Card()
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Service", "Display", "Category", "Status", "Actions"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        card.layout().addWidget(self.table)
        root.addWidget(card, 1)

        self.btn_reload.clicked.connect(self.reload)
        self.combo.currentIndexChanged.connect(self.reload)
        self.reload()

    def reload(self):
        try:
            services = list_services(fill_startup=False)
        except Exception as e:
            QMessageBox.warning(self, "ZetaBoost", f"Failed to enumerate services: {e}")
            return
        cat = self.combo.currentText()
        filtered = [s for s in services if cat == "All" or s.category == cat]
        # Cap to 200 for performance
        filtered = filtered[:200]
        self.table.setRowCount(len(filtered))
        for i, s in enumerate(filtered):
            self.table.setItem(i, 0, QTableWidgetItem(s.name))
            self.table.setItem(i, 1, QTableWidgetItem(s.display))
            self.table.setItem(i, 2, QTableWidgetItem(s.category + (" (critical)" if s.critical else "")))
            self.table.setItem(i, 3, QTableWidgetItem(s.status))
            wrap = QWidget(); h = QHBoxLayout(wrap); h.setContentsMargins(2,2,2,2)
            for mode in ("AUTO", "MANUAL", "DISABLED"):
                b = QPushButton(mode.title())
                if s.critical and mode == "DISABLED":
                    b.setEnabled(False)
                b.clicked.connect(lambda _=False, n=s.name, m=mode: self._change(n, m))
                h.addWidget(b)
            self.table.setCellWidget(i, 4, wrap)

    def _change(self, name, mode):
        ok = set_startup(name, mode)
        QMessageBox.information(self, "ZetaBoost",
                                f"{name}: startup set to {mode}." if ok else "Failed (admin required?)")
