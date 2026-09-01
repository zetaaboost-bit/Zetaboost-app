"""Startup manager page."""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                                QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox)
from app.ui.widgets.cards import SectionHeader, Card
from app.startup.startup_manager import list_startup_items, toggle_startup


class StartupPage(QWidget):
    def __init__(self):
        super().__init__()
        root = QVBoxLayout(self); root.setContentsMargins(28,24,28,24); root.setSpacing(14)
        root.addWidget(SectionHeader("Startup", "Programs that launch with Windows"))

        card = Card()
        h = QHBoxLayout()
        self.btn_reload = QPushButton("Reload")
        h.addStretch(1); h.addWidget(self.btn_reload)
        card.layout().addLayout(h)
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Name", "Location", "Path", "Enabled", "Action"])
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        card.layout().addWidget(self.table)
        root.addWidget(card, 1)

        self.btn_reload.clicked.connect(self.reload)
        self.reload()

    def reload(self):
        try:
            items = list_startup_items()
        except Exception as e:
            QMessageBox.warning(self, "ZetaBoost", f"Failed to enumerate: {e}")
            return
        self.table.setRowCount(len(items))
        for i, it in enumerate(items):
            self.table.setItem(i, 0, QTableWidgetItem(it.name))
            self.table.setItem(i, 1, QTableWidgetItem(it.location))
            self.table.setItem(i, 2, QTableWidgetItem(it.path))
            self.table.setItem(i, 3, QTableWidgetItem("Yes" if it.enabled else "No"))
            b = QPushButton("Disable" if it.enabled else "Enable")
            b.clicked.connect(lambda _=False, item=it: self._toggle(item))
            self.table.setCellWidget(i, 4, b)

    def _toggle(self, item):
        ok = toggle_startup(item, not item.enabled)
        QMessageBox.information(self, "ZetaBoost", "Toggled." if ok else "Failed / HKLM entries need admin.")
        self.reload()
