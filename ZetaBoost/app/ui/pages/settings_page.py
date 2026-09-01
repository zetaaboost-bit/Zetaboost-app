"""Settings page - config + local license toggle."""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox,
                                QComboBox, QSpinBox, QPushButton, QMessageBox, QLineEdit)
from app.ui.widgets.cards import SectionHeader, Card
from app.core.constants import APP_NAME, APP_VERSION


class SettingsPage(QWidget):
    def __init__(self, config, license_mgr):
        super().__init__()
        self.config = config
        self.license_mgr = license_mgr

        root = QVBoxLayout(self); root.setContentsMargins(28,24,28,24); root.setSpacing(14)
        root.addWidget(SectionHeader("Settings", f"{APP_NAME} {APP_VERSION}"))

        c = Card()
        c.layout().addWidget(QLabel("GENERAL"))
        self.chk_start = QCheckBox("Start with Windows"); self.chk_start.setChecked(config.start_with_windows)
        self.chk_tray = QCheckBox("Minimize to tray"); self.chk_tray.setChecked(config.minimize_to_tray)
        self.chk_notif = QCheckBox("Notifications"); self.chk_notif.setChecked(config.notifications)
        self.chk_bkp = QCheckBox("Auto backup before changes"); self.chk_bkp.setChecked(config.auto_backup)
        self.chk_rp = QCheckBox("Auto create Windows Restore Point"); self.chk_rp.setChecked(config.auto_restore_point)
        self.chk_live = QCheckBox("Live Boost auto-detect games (PRO)")
        self.chk_live.setChecked(config.live_boost); self.chk_live.setEnabled(license_mgr.is_pro())
        for w in (self.chk_start, self.chk_tray, self.chk_notif, self.chk_bkp, self.chk_rp, self.chk_live):
            c.layout().addWidget(w)

        row = QHBoxLayout()
        row.addWidget(QLabel("Monitor interval (ms):"))
        self.interval = QSpinBox(); self.interval.setRange(500, 10000); self.interval.setSingleStep(250)
        self.interval.setValue(config.monitor_interval_ms)
        row.addWidget(self.interval); row.addStretch(1)
        c.layout().addLayout(row)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Logging level:"))
        self.lvl = QComboBox(); self.lvl.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.lvl.setCurrentText(config.logging_level)
        row2.addWidget(self.lvl); row2.addStretch(1)
        c.layout().addLayout(row2)

        save_row = QHBoxLayout()
        btn_save = QPushButton("Save"); btn_save.setObjectName("PrimaryButton")
        btn_save.clicked.connect(self._save)
        save_row.addStretch(1); save_row.addWidget(btn_save)
        c.layout().addLayout(save_row)
        root.addWidget(c)

        # License
        lc = Card()
        lc.layout().addWidget(QLabel("LICENSE"))
        lc.layout().addWidget(QLabel(f"Current tier: {license_mgr.tier}   •   HWID: {license_mgr.hwid[:16]}..."))
        row = QHBoxLayout()
        self.key = QLineEdit(); self.key.setPlaceholderText("License key (local mock)")
        btn_activate = QPushButton("Activate as PRO"); btn_activate.setObjectName("PrimaryButton")
        btn_revoke = QPushButton("Revoke to FREE"); btn_revoke.setObjectName("DangerButton")
        btn_activate.clicked.connect(self._activate)
        btn_revoke.clicked.connect(self._revoke)
        row.addWidget(self.key); row.addWidget(btn_activate); row.addWidget(btn_revoke)
        lc.layout().addLayout(row)
        lc.layout().addWidget(QLabel(
            "Note: online license activation, subscription, and login are NOT IMPLEMENTED YET. "
            "The architecture is ready to plug them in."
        ))
        root.addWidget(lc)
        root.addStretch(1)

    def _save(self):
        c = self.config
        c.start_with_windows = self.chk_start.isChecked()
        c.minimize_to_tray = self.chk_tray.isChecked()
        c.notifications = self.chk_notif.isChecked()
        c.auto_backup = self.chk_bkp.isChecked()
        c.auto_restore_point = self.chk_rp.isChecked()
        c.live_boost = self.chk_live.isChecked()
        c.monitor_interval_ms = self.interval.value()
        c.logging_level = self.lvl.currentText()
        c.save()
        QMessageBox.information(self, "ZetaBoost", "Settings saved.")

    def _activate(self):
        self.license_mgr.activate_mock_pro(self.key.text().strip() or "ZETA-PRO-LOCAL")
        QMessageBox.information(self, "ZetaBoost", "Activated as PRO. Restart ZetaBoost to apply UI changes.")

    def _revoke(self):
        self.license_mgr.revoke()
        QMessageBox.information(self, "ZetaBoost", "Reverted to FREE. Restart ZetaBoost.")
