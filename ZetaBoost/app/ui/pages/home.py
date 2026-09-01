"""Home / Dashboard page."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QGridLayout, QVBoxLayout, QHBoxLayout, QLabel

from app.core.constants import COLOR_ACCENT, COLOR_TEXT_DIM
from app.ui.widgets.cards import ScoreGauge, MetricBar, StatCard, SectionHeader, Card
from app.gaming.gaming_mode import is_active as gaming_active
from app.power.power import active_plan_name
from app.optimization.tweak_database import get_tweak, load_builtin_tweaks


class HomePage(QWidget):
    def __init__(self, engine, monitor, license_mgr):
        super().__init__()
        self.engine = engine
        self.monitor = monitor
        self.license_mgr = license_mgr
        load_builtin_tweaks()

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(16)

        head = QHBoxLayout()
        head.addWidget(SectionHeader("Dashboard", "Real-time system overview"))
        head.addStretch(1)
        tier = QLabel("PRO" if license_mgr.is_pro() else "FREE")
        tier.setObjectName("TierPillPro" if license_mgr.is_pro() else "TierPillFree")
        head.addWidget(tier, 0, Qt.AlignTop)
        root.addLayout(head)

        # Top row: score + metrics
        top = QHBoxLayout()
        top.setSpacing(16)
        self.gauge = ScoreGauge()
        top.addWidget(self.gauge, 1)

        metrics_wrap = QVBoxLayout()
        metrics_wrap.setSpacing(10)
        self.cpu_bar = MetricBar("CPU")
        self.ram_bar = MetricBar("RAM")
        self.disk_bar = MetricBar("Disk I/O", unit="MB/s")
        self.net_bar = MetricBar("Network", unit="MB/s")
        for w in (self.cpu_bar, self.ram_bar, self.disk_bar, self.net_bar):
            metrics_wrap.addWidget(w)
        top.addLayout(metrics_wrap, 2)
        root.addLayout(top)

        # Status grid
        root.addWidget(SectionHeader("System Status"))
        grid = QGridLayout()
        grid.setSpacing(12)
        self.card_gaming = StatCard("Gaming Mode", "OFF")
        self.card_gamedvr = StatCard("GameDVR", "--")
        self.card_hags = StatCard("HAGS", "--")
        self.card_power = StatCard("Power Plan", "--")
        for i, c in enumerate((self.card_gaming, self.card_gamedvr, self.card_hags, self.card_power)):
            grid.addWidget(c, 0, i)
        root.addLayout(grid)

        root.addStretch(1)

        # Refresh statuses once + wire monitor
        self._refresh_status_cards()
        monitor.updated.connect(self._on_snapshot)

    def _refresh_status_cards(self) -> None:
        self.card_gaming.set_value("ON" if gaming_active() else "OFF")
        t = get_tweak("gaming.gamedvr_off")
        if t:
            s = t.current_status()
            self.card_gamedvr.set_value("DISABLED" if s == "OFF" else "ENABLED")
        t = get_tweak("gpu.hags_on")
        if t:
            self.card_hags.set_value(t.current_status())
        self.card_power.set_value(active_plan_name())

    def _on_snapshot(self, snap) -> None:
        self.cpu_bar.set_percent(snap.cpu_percent, f"{snap.cpu_percent:.0f} %")
        self.ram_bar.set_percent(snap.ram_percent,
                                 f"{snap.ram_used_gb:.1f} / {snap.ram_total_gb:.1f} GB")
        io = snap.disk_read_mb_s + snap.disk_write_mb_s
        self.disk_bar.set_percent(min(100, io * 5), f"{io:.1f} MB/s")
        net = snap.net_up_mb_s + snap.net_down_mb_s
        self.net_bar.set_percent(min(100, net * 10), f"{net:.2f} MB/s")
        self.gauge.set_score(self.engine.compute_system_score(snap))
