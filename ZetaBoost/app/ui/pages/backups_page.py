"""Backups / Restore page."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                                QListWidget, QListWidgetItem, QPlainTextEdit, QMessageBox)
from app.ui.widgets.cards import SectionHeader, Card
from app.backup.backup import BackupManager
from app.optimization.tweak_database import get_tweak


class BackupsPage(QWidget):
    def __init__(self):
        super().__init__()
        root = QVBoxLayout(self); root.setContentsMargins(28,24,28,24); root.setSpacing(14)
        root.addWidget(SectionHeader("Backups", "Every applied tweak is recorded and reversible"))

        card = Card()
        h = QHBoxLayout()
        self.btn_reload = QPushButton("Reload")
        self.btn_restore_last = QPushButton("RESTORE LAST SESSION"); self.btn_restore_last.setObjectName("PrimaryButton")
        h.addWidget(self.btn_restore_last); h.addStretch(1); h.addWidget(self.btn_reload)
        card.layout().addLayout(h)

        row = QHBoxLayout()
        self.list = QListWidget(); self.list.setMinimumWidth(320)
        self.detail = QPlainTextEdit(); self.detail.setReadOnly(True)
        row.addWidget(self.list, 1); row.addWidget(self.detail, 2)
        card.layout().addLayout(row)
        root.addWidget(card, 1)

        self.btn_reload.clicked.connect(self.reload)
        self.btn_restore_last.clicked.connect(self._restore_last)
        self.list.currentRowChanged.connect(self._show)
        self.sessions = []
        self.reload()

    def reload(self):
        self.sessions = BackupManager.list_sessions()
        self.sessions.sort(key=lambda s: s.get("started_at",""), reverse=True)
        self.list.clear()
        for s in self.sessions:
            self.list.addItem(f"session {s.get('session_id','?')}  ({len(s.get('snapshots',[]))} changes)")

    def _show(self, row):
        if row < 0 or row >= len(self.sessions): self.detail.clear(); return
        import json as _j
        self.detail.setPlainText(_j.dumps(self.sessions[row], indent=2))

    def _restore_last(self):
        if not self.sessions:
            QMessageBox.information(self, "ZetaBoost", "No sessions found."); return
        s = self.sessions[0]
        restored = 0
        for snap in s.get("snapshots", []):
            t = get_tweak(snap["tweak_id"])
            if t and t.restore_fn:
                try:
                    if t.restore().ok: restored += 1
                except Exception: pass
        QMessageBox.information(self, "ZetaBoost", f"Restored {restored} tweak(s) from last session.")
