"""Global QSS stylesheet - dark, gaming, minimal, green accent."""
from PySide6.QtWidgets import QApplication

from app.core.constants import (
    COLOR_BG, COLOR_BG_ELEVATED, COLOR_BG_CARD, COLOR_BORDER,
    COLOR_TEXT, COLOR_TEXT_DIM, COLOR_ACCENT, COLOR_ACCENT_HOVER,
    COLOR_WARN, COLOR_DANGER,
)

QSS_TEMPLATE = """
* {{
    font-family: "Segoe UI", "Inter", "Roboto", sans-serif;
    font-size: 13px;
    color: {text};
    outline: 0;
}}

QMainWindow, QDialog, QWidget#RootWidget {{
    background-color: {bg};
}}

/* Sidebar */
QWidget#Sidebar {{
    background-color: {bg_elev};
    border-right: 1px solid {border};
}}
QLabel#BrandLabel {{
    color: {text};
    font-size: 20px;
    font-weight: 700;
    letter-spacing: 1px;
}}
QLabel#BrandSubLabel {{
    color: {accent};
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 2px;
}}
QLabel#SectionLabel {{
    color: {text_dim};
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 1.5px;
    padding: 12px 18px 6px 18px;
}}

QPushButton#NavButton {{
    background-color: transparent;
    color: {text_dim};
    text-align: left;
    padding: 10px 18px;
    border: none;
    border-left: 3px solid transparent;
    font-size: 13px;
}}
QPushButton#NavButton:hover {{
    background-color: {bg_card};
    color: {text};
}}
QPushButton#NavButton:checked {{
    background-color: {bg_card};
    color: {text};
    border-left: 3px solid {accent};
    font-weight: 600;
}}

/* Cards */
QFrame#Card {{
    background-color: {bg_card};
    border: 1px solid {border};
    border-radius: 12px;
}}
QLabel#CardTitle {{
    font-size: 12px;
    color: {text_dim};
    font-weight: 600;
    letter-spacing: 1px;
}}
QLabel#CardValue {{
    font-size: 22px;
    color: {text};
    font-weight: 700;
}}
QLabel#PageTitle {{
    font-size: 24px;
    font-weight: 700;
    color: {text};
}}
QLabel#PageSubtitle {{
    font-size: 13px;
    color: {text_dim};
}}
QLabel#TierPillFree {{
    background-color: {bg_elev};
    border: 1px solid {border};
    color: {text_dim};
    border-radius: 10px;
    padding: 3px 10px;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1px;
}}
QLabel#TierPillPro {{
    background-color: rgba(46, 232, 143, 0.12);
    border: 1px solid {accent};
    color: {accent};
    border-radius: 10px;
    padding: 3px 10px;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1px;
}}

/* Buttons */
QPushButton {{
    background-color: {bg_card};
    color: {text};
    border: 1px solid {border};
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 600;
}}
QPushButton:hover {{
    border-color: {accent};
    color: {text};
}}
QPushButton:disabled {{
    color: {text_dim};
    background-color: {bg_elev};
    border-color: {border};
}}
QPushButton#PrimaryButton {{
    background-color: {accent};
    color: #0b1015;
    border: none;
}}
QPushButton#PrimaryButton:hover {{
    background-color: {accent_hover};
}}
QPushButton#PrimaryButton:disabled {{
    background-color: {bg_elev};
    color: {text_dim};
}}
QPushButton#DangerButton {{
    background-color: transparent;
    color: {danger};
    border: 1px solid {danger};
}}
QPushButton#DangerButton:hover {{
    background-color: rgba(255, 107, 107, 0.12);
}}
QPushButton#BoostButton {{
    background-color: {accent};
    color: #0b1015;
    border: none;
    font-size: 15px;
    font-weight: 800;
    padding: 14px 26px;
    letter-spacing: 1px;
    border-radius: 10px;
}}
QPushButton#BoostButton:hover {{
    background-color: {accent_hover};
}}

/* Inputs */
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QPlainTextEdit, QTextEdit {{
    background-color: {bg_elev};
    border: 1px solid {border};
    border-radius: 8px;
    padding: 6px 10px;
    color: {text};
    selection-background-color: {accent};
    selection-color: #0b1015;
}}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QPlainTextEdit:focus {{
    border-color: {accent};
}}

/* Progress bars */
QProgressBar {{
    background-color: {bg_elev};
    border: none;
    border-radius: 6px;
    height: 8px;
    text-align: center;
    color: {text};
}}
QProgressBar::chunk {{
    background-color: {accent};
    border-radius: 6px;
}}

/* Tables & Lists */
QTableWidget, QTreeWidget, QListWidget {{
    background-color: {bg_card};
    border: 1px solid {border};
    border-radius: 10px;
    gridline-color: {border};
    alternate-background-color: {bg_elev};
}}
QHeaderView::section {{
    background-color: {bg_elev};
    color: {text_dim};
    border: none;
    border-bottom: 1px solid {border};
    padding: 8px;
    font-weight: 700;
    font-size: 11px;
    letter-spacing: 1px;
}}
QTableWidget::item, QTreeWidget::item, QListWidget::item {{
    padding: 6px;
    border-bottom: 1px solid {border};
}}
QTableWidget::item:selected, QTreeWidget::item:selected, QListWidget::item:selected {{
    background-color: rgba(46, 232, 143, 0.15);
    color: {text};
}}

/* Scrollbars */
QScrollBar:vertical {{
    background: transparent;
    width: 10px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {border};
    min-height: 30px;
    border-radius: 5px;
}}
QScrollBar::handle:vertical:hover {{ background: {text_dim}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}

QScrollBar:horizontal {{ background: transparent; height: 10px; }}
QScrollBar::handle:horizontal {{
    background: {border}; min-width: 30px; border-radius: 5px;
}}
QScrollBar::handle:horizontal:hover {{ background: {text_dim}; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

/* Checkboxes */
QCheckBox {{ spacing: 8px; }}
QCheckBox::indicator {{
    width: 16px; height: 16px;
    border-radius: 4px;
    border: 1px solid {border};
    background-color: {bg_elev};
}}
QCheckBox::indicator:checked {{
    background-color: {accent};
    border-color: {accent};
}}

/* Tabs */
QTabWidget::pane {{
    border: 1px solid {border};
    border-radius: 10px;
    top: -1px;
}}
QTabBar::tab {{
    background: transparent;
    color: {text_dim};
    padding: 8px 16px;
    border: none;
}}
QTabBar::tab:selected {{
    color: {accent};
    border-bottom: 2px solid {accent};
    font-weight: 600;
}}

QToolTip {{
    background-color: {bg_card};
    color: {text};
    border: 1px solid {accent};
    border-radius: 6px;
    padding: 6px 8px;
}}
"""


def apply_dark_theme(app: QApplication) -> None:
    qss = QSS_TEMPLATE.format(
        bg=COLOR_BG,
        bg_elev=COLOR_BG_ELEVATED,
        bg_card=COLOR_BG_CARD,
        border=COLOR_BORDER,
        text=COLOR_TEXT,
        text_dim=COLOR_TEXT_DIM,
        accent=COLOR_ACCENT,
        accent_hover=COLOR_ACCENT_HOVER,
        warn=COLOR_WARN,
        danger=COLOR_DANGER,
    )
    app.setStyleSheet(qss)
