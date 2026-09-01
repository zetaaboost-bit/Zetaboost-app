"""Network page."""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                                QLineEdit, QPlainTextEdit, QMessageBox)
from app.ui.widgets.cards import SectionHeader, Card
from app.network.network import (list_interfaces, default_gateway, dns_servers,
                                  ping, flush_dns, winsock_reset, tcpip_reset)


class NetworkPage(QWidget):
    def __init__(self):
        super().__init__()
        root = QVBoxLayout(self); root.setContentsMargins(28,24,28,24); root.setSpacing(14)
        root.addWidget(SectionHeader("Network", "Diagnose, tune, and repair Windows networking"))

        info = Card()
        info.layout().addWidget(QLabel("ADAPTERS"))
        text = QPlainTextEdit(); text.setReadOnly(True); text.setMaximumHeight(150)
        lines = []
        for i in list_interfaces():
            if i.ipv4 or i.is_up:
                lines.append(f"  {i.name:<25}  {i.ipv4:<15}  {'UP' if i.is_up else 'DOWN'}  {i.speed_mbps} Mbps")
        lines.append(f"\n  Gateway: {default_gateway()}")
        lines.append(f"  DNS: {', '.join(dns_servers()) or 'auto'}")
        text.setPlainText("\n".join(lines))
        info.layout().addWidget(text)
        root.addWidget(info)

        # Ping
        c = Card()
        c.layout().addWidget(QLabel("PING TEST"))
        h = QHBoxLayout()
        self.host = QLineEdit(); self.host.setPlaceholderText("host (e.g. 1.1.1.1)")
        self.host.setText("1.1.1.1")
        btn_ping = QPushButton("Ping"); btn_ping.setObjectName("PrimaryButton")
        h.addWidget(self.host); h.addWidget(btn_ping)
        c.layout().addLayout(h)
        self.ping_out = QPlainTextEdit(); self.ping_out.setReadOnly(True); self.ping_out.setMaximumHeight(140)
        c.layout().addWidget(self.ping_out)
        btn_ping.clicked.connect(self._ping)
        root.addWidget(c)

        # Repair tools
        r = Card()
        r.layout().addWidget(QLabel("REPAIR TOOLS"))
        hr = QHBoxLayout()
        for label, fn in [("Flush DNS", flush_dns), ("Winsock Reset", winsock_reset),
                          ("TCP/IP Reset", tcpip_reset)]:
            b = QPushButton(label)
            b.clicked.connect(lambda _=False, f=fn, name=label: self._run(f, name))
            hr.addWidget(b)
        hr.addStretch(1)
        r.layout().addLayout(hr)
        root.addWidget(r)
        root.addStretch(1)

    def _ping(self):
        res = ping(self.host.text().strip() or "1.1.1.1")
        self.ping_out.setPlainText(res.raw or "No output.")

    def _run(self, fn, name):
        ok = fn()
        QMessageBox.information(self, "ZetaBoost",
                                f"{name}: {'success' if ok else 'failed or not available'}")
