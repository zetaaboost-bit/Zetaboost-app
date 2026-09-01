"""Reusable UI widgets: Card, StatCard, MetricBar, ScoreGauge, SectionHeader."""
from typing import Optional

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPainter, QPen, QColor, QFont, QConicalGradient
from PySide6.QtWidgets import (
    QFrame, QLabel, QVBoxLayout, QHBoxLayout, QProgressBar, QWidget, QSizePolicy
)

from app.core.constants import COLOR_ACCENT, COLOR_BORDER, COLOR_TEXT_DIM, COLOR_TEXT


class Card(QFrame):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("Card")
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(18, 16, 18, 16)
        self._layout.setSpacing(10)

    def layout(self) -> QVBoxLayout:  # type: ignore[override]
        return self._layout


class SectionHeader(QWidget):
    def __init__(self, title: str, subtitle: str = "", parent: Optional[QWidget] = None):
        super().__init__(parent)
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 4)
        v.setSpacing(2)
        t = QLabel(title)
        t.setObjectName("PageTitle")
        v.addWidget(t)
        if subtitle:
            s = QLabel(subtitle)
            s.setObjectName("PageSubtitle")
            v.addWidget(s)


class StatCard(Card):
    def __init__(self, title: str, initial_value: str = "--", parent=None):
        super().__init__(parent)
        self.title_lbl = QLabel(title.upper())
        self.title_lbl.setObjectName("CardTitle")
        self.value_lbl = QLabel(initial_value)
        self.value_lbl.setObjectName("CardValue")
        self.layout().addWidget(self.title_lbl)
        self.layout().addWidget(self.value_lbl)
        self.layout().addStretch(1)
        self.setMinimumHeight(96)

    def set_value(self, v: str) -> None:
        self.value_lbl.setText(v)


class MetricBar(Card):
    def __init__(self, title: str, unit: str = "%", parent=None):
        super().__init__(parent)
        self.unit = unit
        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)
        self.title_lbl = QLabel(title.upper())
        self.title_lbl.setObjectName("CardTitle")
        self.value_lbl = QLabel(f"0 {unit}")
        self.value_lbl.setStyleSheet(f"color:{COLOR_TEXT}; font-weight:700;")
        top.addWidget(self.title_lbl)
        top.addStretch(1)
        top.addWidget(self.value_lbl)

        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self.bar.setValue(0)
        self.bar.setTextVisible(False)
        self.bar.setFixedHeight(8)

        self.layout().addLayout(top)
        self.layout().addWidget(self.bar)
        self.setMinimumHeight(84)

    def set_percent(self, p: float, display: str = "") -> None:
        p = max(0.0, min(100.0, float(p)))
        self.bar.setValue(int(p))
        self.value_lbl.setText(display or f"{p:.0f} {self.unit}")


class ScoreGauge(QWidget):
    """Simple circular score gauge - 0 to 100."""
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._score = 0
        self.setMinimumSize(220, 220)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

    def set_score(self, s: int) -> None:
        self._score = max(0, min(100, int(s)))
        self.update()

    def paintEvent(self, e) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        side = min(self.width(), self.height()) - 20
        rect = QRectF((self.width() - side) / 2, (self.height() - side) / 2, side, side)

        # Track
        pen = QPen(QColor(COLOR_BORDER), 14, Qt.SolidLine, Qt.RoundCap)
        p.setPen(pen)
        p.drawArc(rect, 0, 360 * 16)

        # Fill according to score
        color = QColor(COLOR_ACCENT)
        if self._score < 50:
            color = QColor("#ff6b6b")
        elif self._score < 75:
            color = QColor("#f0b429")
        pen = QPen(color, 14, Qt.SolidLine, Qt.RoundCap)
        p.setPen(pen)
        p.drawArc(rect, 90 * 16, -int(3.6 * self._score) * 16)

        # Score text
        p.setPen(QColor(COLOR_TEXT))
        f = QFont()
        f.setPointSize(36)
        f.setBold(True)
        p.setFont(f)
        p.drawText(rect, Qt.AlignCenter, str(self._score))

        # Label
        p.setPen(QColor(COLOR_TEXT_DIM))
        f2 = QFont()
        f2.setPointSize(9)
        f2.setBold(True)
        f2.setLetterSpacing(QFont.PercentageSpacing, 130)
        p.setFont(f2)
        p.drawText(rect.adjusted(0, side * 0.32, 0, 0), Qt.AlignHCenter | Qt.AlignTop, "SYSTEM SCORE")
