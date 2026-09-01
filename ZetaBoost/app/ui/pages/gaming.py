"""Gaming page: Gaming Mode toggle + profiles + Live Boost."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                                QListWidget, QListWidgetItem, QMessageBox, QCheckBox)
from app.ui.widgets.cards import SectionHeader, Card
from app.gaming.gaming_mode import enable as gm_enable, disable as gm_disable, is_active
from app.gaming.profiles import load_all, GameProfile, upsert
from app.gaming.live_boost import LiveBoostService


class GamingPage(QWidget):
    def __init__(self, license_mgr):
        super().__init__()
        self.license_mgr = license_mgr
        self.live_boost = LiveBoostService()

        root = QVBoxLayout(self); root.setContentsMargins(28,24,28,24); root.setSpacing(14)
        root.addWidget(SectionHeader("Gaming Mode", "Reversible gaming optimizations and profiles"))

        # Gaming Mode
        card = Card()
        h = QHBoxLayout()
        self.state_lbl = QLabel()
        self.state_lbl.setStyleSheet("font-size:15px; font-weight:700;")
        self.btn_toggle = QPushButton()
        self.btn_toggle.setObjectName("PrimaryButton")
        h.addWidget(self.state_lbl); h.addStretch(1); h.addWidget(self.btn_toggle)
        card.layout().addLayout(h)
        info = QLabel("Applies GameDVR off, Game Mode on, mouse acceleration off, "
                      "and visual effects → performance. Fully reversible.")
        info.setWordWrap(True); info.setStyleSheet("color:#8b949e;")
        card.layout().addWidget(info)
        root.addWidget(card)
        self.btn_toggle.clicked.connect(self._toggle)
        self._refresh_state()

        # Profiles
        card2 = Card()
        card2.layout().addWidget(QLabel("GAME PROFILES"))
        self.profile_list = QListWidget()
        self.profile_list.setMinimumHeight(220)
        card2.layout().addWidget(self.profile_list)
        h2 = QHBoxLayout()
        btn_new = QPushButton("Create Custom Profile")
        btn_apply = QPushButton("Apply Profile"); btn_apply.setObjectName("PrimaryButton")
        h2.addWidget(btn_new); h2.addStretch(1); h2.addWidget(btn_apply)
        card2.layout().addLayout(h2)
        root.addWidget(card2)
        self._load_profiles()
        btn_new.clicked.connect(self._new_profile)
        btn_apply.clicked.connect(self._apply_profile)

        # Live Boost (PRO)
        card3 = Card()
        lb_row = QHBoxLayout()
        lbl = QLabel("LIVE BOOST"); lbl.setStyleSheet("font-weight:700;")
        self.lb_chk = QCheckBox("Enable Live Boost (auto-apply profile when a game launches)")
        if not license_mgr.is_pro():
            self.lb_chk.setEnabled(False); self.lb_chk.setText(self.lb_chk.text() + "   [PRO]")
        lb_row.addWidget(lbl); lb_row.addStretch(1)
        card3.layout().addLayout(lb_row)
        card3.layout().addWidget(self.lb_chk)
        self.lb_status = QLabel("Idle."); self.lb_status.setStyleSheet("color:#8b949e;")
        card3.layout().addWidget(self.lb_status)
        root.addWidget(card3)
        self.lb_chk.toggled.connect(self._toggle_live)
        self.live_boost.logMessage.connect(self.lb_status.setText)

        root.addStretch(1)

    def _refresh_state(self):
        active = is_active()
        self.state_lbl.setText(f"Status: {'ACTIVE' if active else 'INACTIVE'}")
        self.btn_toggle.setText("DISABLE" if active else "ENABLE")

    def _toggle(self):
        if is_active():
            gm_disable(); QMessageBox.information(self, "ZetaBoost", "Gaming Mode disabled.")
        else:
            gm_enable();  QMessageBox.information(self, "ZetaBoost", "Gaming Mode enabled.")
        self._refresh_state()

    def _load_profiles(self):
        self.profile_list.clear()
        for p in load_all():
            it = QListWidgetItem(f"  {p.display_name}   ({p.process_name or 'no process'})")
            it.setData(Qt.UserRole, p.id)
            self.profile_list.addItem(it)

    def _new_profile(self):
        # Quick create using timestamp id
        from datetime import datetime
        pid = f"custom_{datetime.now().strftime('%H%M%S')}"
        p = GameProfile(id=pid, display_name=f"Custom {pid}", process_name="",
                        tweak_ids=["gaming.gamedvr_off"], custom=True)
        upsert(p); self._load_profiles()
        QMessageBox.information(self, "ZetaBoost", f"Custom profile '{pid}' created.")

    def _apply_profile(self):
        it = self.profile_list.currentItem()
        if not it: return
        from app.optimization.tweak_database import get_tweak
        from app.gaming.profiles import get
        prof = get(it.data(Qt.UserRole))
        if not prof: return
        applied = 0
        for tid in prof.tweak_ids:
            t = get_tweak(tid)
            if t and t.apply_fn and (t.tier != "PRO" or self.license_mgr.is_pro()):
                if t.apply().ok: applied += 1
        QMessageBox.information(self, "ZetaBoost",
                                f"Profile '{prof.display_name}' applied ({applied} tweaks).")

    def _toggle_live(self, on):
        if on: self.live_boost.start()
        else:  self.live_boost.stop()
