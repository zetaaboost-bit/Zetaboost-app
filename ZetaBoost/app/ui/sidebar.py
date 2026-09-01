"""Sidebar navigation."""
from typing import List, Tuple

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QButtonGroup,
    QScrollArea, QFrame
)

from app.core.constants import APP_NAME


NAV: List[Tuple[str, str, str]] = [
    # (section, key, label)
    ("MAIN",       "home",        "Home"),
    ("MAIN",       "my_pc",       "My PC"),
    ("MAIN",       "boost",       "Boost"),
    ("MAIN",       "optimize",    "Optimize"),
    ("GAMING",     "gaming",      "Gaming"),
    ("CLEAN",      "cleaner",     "Cleaner"),
    ("CLEAN",      "storage",     "Storage"),
    ("SYSTEM",     "network",     "Network"),
    ("SYSTEM",     "memory",      "Memory"),
    ("SYSTEM",     "gpu",         "GPU"),
    ("SYSTEM",     "cpu",         "CPU"),
    ("SYSTEM",     "services",    "Services"),
    ("SYSTEM",     "startup",     "Startup"),
    ("SECURE",     "privacy",     "Privacy"),
    ("SECURE",     "repair",      "Repair"),
    ("SECURE",     "diagnostics", "Diagnostics"),
    ("SECURE",     "backups",     "Backups"),
    ("EXTRA",      "tools",       "Tools"),
    ("EXTRA",      "settings",    "Settings"),
]


class Sidebar(QWidget):
    navigated = Signal(str)   # key

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(228)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 20, 0, 20)
        root.setSpacing(0)

        # Brand
        brand_wrap = QVBoxLayout()
        brand_wrap.setContentsMargins(18, 0, 18, 20)
        brand_wrap.setSpacing(0)
        brand = QLabel(APP_NAME.upper())
        brand.setObjectName("BrandLabel")
        sub = QLabel("PRECISION OPTIMIZATION")
        sub.setObjectName("BrandSubLabel")
        brand_wrap.addWidget(brand)
        brand_wrap.addWidget(sub)
        root.addLayout(brand_wrap)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        content = QWidget()
        v = QVBoxLayout(content)
        v.setContentsMargins(0, 0, 0, 8)
        v.setSpacing(0)

        self.group = QButtonGroup(self)
        self.group.setExclusive(True)
        self.buttons = {}

        current_section = None
        for section, key, label in NAV:
            if section != current_section:
                lbl = QLabel(section)
                lbl.setObjectName("SectionLabel")
                v.addWidget(lbl)
                current_section = section
            btn = QPushButton(label)
            btn.setObjectName("NavButton")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _=False, k=key: self.navigated.emit(k))
            self.group.addButton(btn)
            self.buttons[key] = btn
            v.addWidget(btn)

        v.addStretch(1)
        scroll.setWidget(content)
        root.addWidget(scroll, 1)

    def select(self, key: str) -> None:
        btn = self.buttons.get(key)
        if btn:
            btn.setChecked(True)
