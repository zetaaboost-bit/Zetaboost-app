"""Main window - hosts sidebar + stacked pages + top status bar."""
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget, QLabel,
    QStatusBar
)

from app.core.constants import APP_NAME, APP_VERSION, APP_TAGLINE
from app.core.admin import is_admin
from app.core.logger import get_logger
from app.hardware.detector import collect_hardware_report
from app.hardware.monitor import SystemMonitor
from app.optimization.engine import OptimizationEngine

from app.ui.sidebar import Sidebar
from app.ui.pages.home import HomePage
from app.ui.pages.my_pc import MyPCPage
from app.ui.pages.boost import BoostPage
from app.ui.pages.optimize import OptimizePage
from app.ui.pages.gaming import GamingPage
from app.ui.pages.cleaner import CleanerPage
from app.ui.pages.network import NetworkPage
from app.ui.pages.memory import MemoryPage
from app.ui.pages.gpu_page import GPUPage
from app.ui.pages.cpu_page import CPUPage
from app.ui.pages.storage_page import StoragePage
from app.ui.pages.services_page import ServicesPage
from app.ui.pages.startup_page import StartupPage
from app.ui.pages.privacy_page import PrivacyPage
from app.ui.pages.repair_page import RepairPage
from app.ui.pages.tools_page import ToolsPage
from app.ui.pages.diagnostics_page import DiagnosticsPage
from app.ui.pages.backups_page import BackupsPage
from app.ui.pages.settings_page import SettingsPage

log = get_logger("ui.main")


class MainWindow(QMainWindow):
    def __init__(self, config, license_mgr):
        super().__init__()
        self.config = config
        self.license_mgr = license_mgr

        self.setWindowTitle(f"{APP_NAME} {APP_VERSION}")
        self.resize(1240, 780)
        self.setMinimumSize(1080, 680)

        # Core services
        self.hw_report = collect_hardware_report()
        self.engine = OptimizationEngine(license_mgr=license_mgr, hw_report=self.hw_report)
        self.monitor = SystemMonitor(interval_ms=config.monitor_interval_ms)

        # Layout root
        root = QWidget()
        root.setObjectName("RootWidget")
        h = QHBoxLayout(root)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(0)

        self.sidebar = Sidebar()
        self.stack = QStackedWidget()

        h.addWidget(self.sidebar)
        h.addWidget(self.stack, 1)
        self.setCentralWidget(root)

        # Pages
        self.pages = {}
        self._add_page("home",        HomePage(self.engine, self.monitor, license_mgr))
        self._add_page("my_pc",       MyPCPage(self.hw_report))
        self._add_page("boost",       BoostPage(self.engine, license_mgr))
        self._add_page("optimize",    OptimizePage(self.engine, license_mgr))
        self._add_page("gaming",      GamingPage(license_mgr))
        self._add_page("cleaner",     CleanerPage(license_mgr))
        self._add_page("network",     NetworkPage())
        self._add_page("memory",      MemoryPage(self.monitor))
        self._add_page("gpu",         GPUPage(self.hw_report, license_mgr))
        self._add_page("cpu",         CPUPage(self.hw_report, license_mgr))
        self._add_page("storage",     StoragePage(self.hw_report, license_mgr))
        self._add_page("services",    ServicesPage(license_mgr))
        self._add_page("startup",     StartupPage())
        self._add_page("privacy",     PrivacyPage(self.engine, license_mgr))
        self._add_page("repair",      RepairPage(license_mgr))
        self._add_page("tools",       ToolsPage())
        self._add_page("diagnostics", DiagnosticsPage())
        self._add_page("backups",     BackupsPage())
        self._add_page("settings",    SettingsPage(config, license_mgr))

        self.sidebar.navigated.connect(self.navigate)
        self.sidebar.select("home")
        self.navigate("home")

        # Status bar
        sb = QStatusBar()
        self.setStatusBar(sb)
        admin_txt = "Administrator" if is_admin() else "Standard user (limited tweaks)"
        tier_txt = "PRO" if license_mgr.is_pro() else "FREE"
        sb.showMessage(f"  {APP_TAGLINE}   •   Tier: {tier_txt}   •   {admin_txt}")

        # Start monitor
        self.monitor.start()

    def _add_page(self, key: str, page: QWidget) -> None:
        self.pages[key] = page
        self.stack.addWidget(page)

    def navigate(self, key: str) -> None:
        w = self.pages.get(key)
        if w:
            self.stack.setCurrentWidget(w)
            log.info(f"navigate -> {key}")

    def closeEvent(self, e) -> None:  # noqa: N802
        try:
            self.monitor.stop()
        except Exception:
            pass
        super().closeEvent(e)
