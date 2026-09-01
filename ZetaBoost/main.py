"""
ZetaBoost - Windows PC Optimization Suite
Entry point of the application.
"""
import sys
import os

# Ensure project root is on sys.path when frozen / launched from anywhere
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt

from app.core.constants import APP_NAME, APP_VERSION, ASSETS_DIR
from app.core.theme import apply_dark_theme
from app.core.logger import init_logger, get_logger
from app.core.config import Config
from app.core.license import LicenseManager
from app.core.admin import is_admin, request_admin_relaunch
from app.ui.main_window import MainWindow


def main() -> int:
    # High-DPI support (Qt6 handles this automatically but be explicit)
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName("ZetaBoost")

    # Icon
    icon_path = os.path.join(ASSETS_DIR, "icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # Init logger & config
    init_logger()
    log = get_logger("main")
    log.info(f"Starting {APP_NAME} v{APP_VERSION}")

    config = Config.load()
    license_mgr = LicenseManager.load()

    log.info(f"License tier: {license_mgr.tier}")
    log.info(f"Admin privileges: {is_admin()}")

    apply_dark_theme(app)

    win = MainWindow(config=config, license_mgr=license_mgr)
    win.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
