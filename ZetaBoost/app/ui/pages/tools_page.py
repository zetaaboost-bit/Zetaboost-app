"""Tools page - misc utilities."""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QMessageBox
from app.ui.widgets.cards import SectionHeader, Card
from app.backup.backup import BackupManager


class ToolsPage(QWidget):
    def __init__(self):
        super().__init__()
        root = QVBoxLayout(self); root.setContentsMargins(28,24,28,24); root.setSpacing(14)
        root.addWidget(SectionHeader("Tools", "Additional utilities"))

        c = Card()
        c.layout().addWidget(QLabel("SYSTEM RESTORE POINT"))
        c.layout().addWidget(QLabel("Create a Windows System Restore Point before making changes."))
        row = QHBoxLayout()
        b = QPushButton("Create Restore Point"); b.setObjectName("PrimaryButton")
        b.clicked.connect(self._restore_point)
        row.addWidget(b); row.addStretch(1)
        c.layout().addLayout(row)
        root.addWidget(c)

        c2 = Card()
        c2.layout().addWidget(QLabel("ADVANCED (COMING SOON)"))
        c2.layout().addWidget(QLabel("Debloat catalog, deep Windows Update reset, driver review — NOT IMPLEMENTED YET."))
        root.addWidget(c2)
        root.addStretch(1)

    def _restore_point(self):
        mgr = BackupManager()
        ok = mgr.create_system_restore_point()
        QMessageBox.information(self, "ZetaBoost",
                                "Restore point created." if ok else
                                "Failed: needs admin + System Restore enabled on system drive.")
