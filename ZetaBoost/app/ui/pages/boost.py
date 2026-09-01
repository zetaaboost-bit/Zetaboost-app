"""One-Click Boost page."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                                QListWidget, QListWidgetItem, QMessageBox, QCheckBox)
from app.ui.widgets.cards import SectionHeader, Card
from app.core.constants import TIER_PRO


class BoostPage(QWidget):
    def __init__(self, engine, license_mgr):
        super().__init__()
        self.engine = engine
        self.license_mgr = license_mgr

        root = QVBoxLayout(self); root.setContentsMargins(28,24,28,24); root.setSpacing(14)
        root.addWidget(SectionHeader("One-Click Boost", "Scan, review, and apply recommended optimizations"))

        card = Card()
        h = QHBoxLayout()
        self.btn_scan = QPushButton("SCAN MY PC"); self.btn_scan.setObjectName("BoostButton")
        self.btn_apply = QPushButton("APPLY RECOMMENDED"); self.btn_apply.setObjectName("PrimaryButton")
        self.btn_apply.setEnabled(False)
        h.addWidget(self.btn_scan); h.addWidget(self.btn_apply); h.addStretch(1)
        card.layout().addLayout(h)

        self.summary = QLabel("Click SCAN to detect recommendations for your system.")
        self.summary.setStyleSheet("color:#8b949e;")
        card.layout().addWidget(self.summary)

        self.list = QListWidget()
        self.list.setMinimumHeight(320)
        card.layout().addWidget(self.list)
        root.addWidget(card)

        self.btn_scan.clicked.connect(self.on_scan)
        self.btn_apply.clicked.connect(self.on_apply)

    def on_scan(self):
        self.list.clear()
        recs = self.engine.recommended_tweaks()
        if not recs:
            self.summary.setText("No recommendations found. Your system looks good!")
            self.btn_apply.setEnabled(False)
            return
        counts = {}
        for t in recs:
            counts[t.category] = counts.get(t.category, 0) + 1
            item = QListWidgetItem(f"  ✓  [{t.category}]  {t.name}  —  risk: {t.risk}")
            item.setData(Qt.UserRole, t.id)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked)
            self.list.addItem(item)
        parts = ", ".join(f"{v} {k.lower()}" for k, v in counts.items())
        self.summary.setText(f"Found {len(recs)} recommendation(s): {parts}")
        self.btn_apply.setEnabled(True)

    def on_apply(self):
        selected = []
        for i in range(self.list.count()):
            it = self.list.item(i)
            if it.checkState() == Qt.Checked:
                selected.append(it.data(Qt.UserRole))
        if not selected:
            return
        ok = fail = 0
        for tid in selected:
            r = self.engine.apply_tweak(tid)
            if r.ok: ok += 1
            else: fail += 1
        QMessageBox.information(self, "ZetaBoost", f"Applied: {ok}\nFailed / skipped: {fail}")
        self.on_scan()
