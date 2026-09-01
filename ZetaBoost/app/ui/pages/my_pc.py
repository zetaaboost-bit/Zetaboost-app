"""My PC page - hardware summary."""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel
from app.ui.widgets.cards import SectionHeader, Card


def _kv(label, value):
    l = QLabel(label.upper()); l.setObjectName("CardTitle")
    v = QLabel(str(value)); v.setStyleSheet("font-size:14px; font-weight:600;")
    return l, v


class MyPCPage(QWidget):
    def __init__(self, hw):
        super().__init__()
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(16)
        root.addWidget(SectionHeader("My PC", "Detected hardware and Windows information"))

        # CPU
        cpu = Card()
        g = QGridLayout(); g.setHorizontalSpacing(30); g.setVerticalSpacing(6)
        rows = [
            ("Name", hw.cpu.name), ("Vendor", hw.cpu.vendor),
            ("Manufacturer", hw.cpu.manufacturer or "-"),
            ("Cores", hw.cpu.cores), ("Threads", hw.cpu.threads),
            ("Clock", f"{hw.cpu.base_clock_mhz} MHz" if hw.cpu.base_clock_mhz else "-"),
            ("Architecture", hw.cpu.architecture or "-"),
        ]
        for i,(k,v) in enumerate(rows):
            lk, lv = _kv(k, v); g.addWidget(lk, i, 0); g.addWidget(lv, i, 1)
        cpu_title = QLabel("CPU"); cpu_title.setObjectName("CardTitle")
        cpu.layout().addWidget(cpu_title); cpu.layout().addLayout(g)
        root.addWidget(cpu)

        # GPUs
        for gpu in hw.gpus:
            c = Card(); g2 = QGridLayout(); g2.setHorizontalSpacing(30); g2.setVerticalSpacing(6)
            rows = [("Name", gpu.name), ("Vendor", gpu.vendor),
                    ("VRAM", f"{gpu.vram_mb} MB" if gpu.vram_mb else "-"),
                    ("Driver", gpu.driver_version or "-")]
            for i,(k,v) in enumerate(rows):
                lk,lv=_kv(k,v); g2.addWidget(lk,i,0); g2.addWidget(lv,i,1)
            t = QLabel("GPU"); t.setObjectName("CardTitle")
            c.layout().addWidget(t); c.layout().addLayout(g2)
            root.addWidget(c)

        # RAM
        c = Card(); g = QGridLayout(); g.setHorizontalSpacing(30); g.setVerticalSpacing(6)
        for i,(k,v) in enumerate([("Total", f"{hw.ram.total_gb} GB"),
                                  ("Used", f"{hw.ram.used_gb} GB ({hw.ram.percent}%)"),
                                  ("Available", f"{hw.ram.available_gb} GB")]):
            lk,lv=_kv(k,v); g.addWidget(lk,i,0); g.addWidget(lv,i,1)
        t=QLabel("RAM"); t.setObjectName("CardTitle")
        c.layout().addWidget(t); c.layout().addLayout(g); root.addWidget(c)

        # Storage
        for d in hw.disks:
            c=Card(); g=QGridLayout(); g.setHorizontalSpacing(30); g.setVerticalSpacing(6)
            rows=[("Device", d.device), ("Media", d.media_type),
                  ("Filesystem", d.fstype), ("Total", f"{d.total_gb} GB"),
                  ("Free", f"{d.free_gb} GB ({100-d.percent:.0f}% free)")]
            for i,(k,v) in enumerate(rows):
                lk,lv=_kv(k,v); g.addWidget(lk,i,0); g.addWidget(lv,i,1)
            t=QLabel(f"STORAGE - {d.mountpoint}"); t.setObjectName("CardTitle")
            c.layout().addWidget(t); c.layout().addLayout(g); root.addWidget(c)

        # Windows
        c=Card(); g=QGridLayout(); g.setHorizontalSpacing(30); g.setVerticalSpacing(6)
        for i,(k,v) in enumerate([("Name", hw.os.name), ("Version", hw.os.version),
                                  ("Build", hw.os.build or "-"), ("Arch", hw.os.architecture),
                                  ("Install Date", hw.os.install_date or "-")]):
            lk,lv=_kv(k,v); g.addWidget(lk,i,0); g.addWidget(lv,i,1)
        t=QLabel("WINDOWS"); t.setObjectName("CardTitle")
        c.layout().addWidget(t); c.layout().addLayout(g); root.addWidget(c)

        root.addStretch(1)
