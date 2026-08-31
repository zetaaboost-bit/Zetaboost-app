"""
ZetaBoost Elite Suite v2.1
App de optimización de Windows orientada a gaming competitivo
(Fortnite prioritario + shooters en general)

Mejoras v2.1:
- UI más cercana a nivel VoltX
- Más tweaks útiles (latencia, GPU, red, sistema)
- Mejor organización y experiencia de usuario
"""

import ctypes
import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

import customtkinter as ctk
import psutil

# ==================== CONFIG ====================
APP_NAME = "ZetaBoost"
APP_VERSION = "2.1"
CONFIG_DIR = Path(os.environ.get("APPDATA", ".")) / "ZetaBoost"
CONFIG_FILE = CONFIG_DIR / "config.json"

# Colores (negro + verde - estilo premium)
COLOR_BG = "#06080c"
COLOR_SIDEBAR = "#0b1017"
COLOR_CARD = "#111821"
COLOR_CARD_HOVER = "#161f2b"
COLOR_GREEN = "#00ff88"
COLOR_GREEN_HOVER = "#00e07a"
COLOR_GREEN_DIM = "#00c96e"
COLOR_TEXT = "#f0f4f8"
COLOR_TEXT_MUTED = "#8b9cb3"
COLOR_TEXT_DIM = "#5c6b7e"
COLOR_BORDER = "#1a2433"
COLOR_DANGER = "#ff4757"
COLOR_WARNING = "#ffa502"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")


# ==================== UTILIDADES ====================
def es_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def relanzar_como_admin():
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, " ".join(sys.argv), None, 1
    )
    sys.exit()


def correr(cmd: str) -> bool:
    try:
        r = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            timeout=180,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        return r.returncode == 0
    except Exception:
        return False


def cargar_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def guardar_config(data: dict):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    actual = cargar_config()
    actual.update(data)
    CONFIG_FILE.write_text(json.dumps(actual, indent=2), encoding="utf-8")


# ==================== CATÁLOGO DE TWEAKS ====================
# (nombre, descripción, comandos)

TWEAKS_FREE = {
    "Limpieza": [
        (
            "Limpieza profunda de temporales",
            "Borra temporales de Windows, Prefetch y papelera de reciclaje.",
            [
                'del /s /f /q "%TEMP%\\*" 2>nul',
                'rd /s /q "%TEMP%" & md "%TEMP%" 2>nul',
                'del /s /f /q "C:\\Windows\\Temp\\*" 2>nul',
                'del /s /f /q "C:\\Windows\\Prefetch\\*" 2>nul',
                'PowerShell -NoProfile -Command "Clear-RecycleBin -Force -ErrorAction SilentlyContinue"',
            ],
        ),
        (
            "Purga de cache de shaders",
            "Limpia caches de DirectX, NVIDIA y AMD. Recomendado después de actualizar drivers.",
            [
                'del /s /f /q "%LOCALAPPDATA%\\D3DSCache\\*" 2>nul',
                'del /s /f /q "%LOCALAPPDATA%\\NVIDIA\\DXCache\\*" 2>nul',
                'del /s /f /q "%LOCALAPPDATA%\\NVIDIA\\GLCache\\*" 2>nul',
                'del /s /f /q "%LOCALAPPDATA%\\AMD\\DxCache\\*" 2>nul',
                'del /s /f /q "%LOCALAPPDATA%\\AMD\\GLCache\\*" 2>nul',
            ],
        ),
        (
            "Limpieza de Delivery Optimization",
            "Elimina archivos residuales de actualizaciones de Windows.",
            [
                'del /s /f /q "C:\\Windows\\SoftwareDistribution\\Download\\*" 2>nul',
            ],
        ),
    ],
    "Gaming Básico": [
        (
            "Desactivar GameDVR y Game Bar",
            "Elimina la grabación de fondo que consume CPU/GPU y añade latencia.",
            [
                'reg add "HKCU\\System\\GameConfigStore" /v "GameDVR_Enabled" /t REG_DWORD /d 0 /f',
                'reg add "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\GameDVR" /v "AppCaptureEnabled" /t REG_DWORD /d 0 /f',
                'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\GameDVR" /v "AllowGameDVR" /t REG_DWORD /d 0 /f',
                'reg add "HKCU\\SOFTWARE\\Microsoft\\GameBar" /v "ShowStartupPanel" /t REG_DWORD /d 0 /f',
            ],
        ),
        (
            "Perfil de energía Ultimate Performance",
            "Activa el plan de máxima potencia de Windows (si está disponible).",
            [
                'powercfg -duplicatescheme e9a42b02-d5df-448d-aa00-03f14749eb61 >nul 2>&1',
                'for /f "tokens=*" %i in (\'powercfg -list ^| findstr /i "Ultimate"\') do powercfg /setactive %i',
            ],
        ),
        (
            "Acelerar menús y desactivar animaciones",
            "Reduce el delay de menús contextuales y elimina animaciones innecesarias.",
            [
                'reg add "HKCU\\Control Panel\\Desktop" /v "MenuShowDelay" /t REG_SZ /d "0" /f',
                'reg add "HKCU\\Control Panel\\Desktop\\WindowMetrics" /v "MinAnimate" /t REG_SZ /d "0" /f',
                'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced" /v "ListviewAlphaSelect" /t REG_DWORD /d 0 /f',
                'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced" /v "ListviewShadow" /t REG_DWORD /d 0 /f',
            ],
        ),
        (
            "Desactivar Fullscreen Optimizations (por usuario)",
            "Evita que Windows interfiera con juegos en pantalla completa.",
            [
                'reg add "HKCU\\System\\GameConfigStore" /v "GameDVR_FSEBehaviorMode" /t REG_DWORD /d 2 /f',
                'reg add "HKCU\\System\\GameConfigStore" /v "GameDVR_HonorUserFSEBehaviorMode" /t REG_DWORD /d 1 /f',
                'reg add "HKCU\\System\\GameConfigStore" /v "GameDVR_FSEBehavior" /t REG_DWORD /d 2 /f',
            ],
        ),
    ],
    "Red Básica": [
        (
            "Flush DNS + Reset de red",
            "Limpia caché DNS y reinicia la pila de red. Útil con ping alto o packet loss.",
            [
                "ipconfig /flushdns",
                "ipconfig /registerdns",
                "netsh winsock reset",
                "netsh int ip reset",
                "netsh int tcp reset",
            ],
        ),
        (
            "Optimizar DNS (Cloudflare + Google)",
            "Configura DNS rápidos y confiables.",
            [
                'netsh interface ip set dns "Ethernet" static 1.1.1.1 primary',
                'netsh interface ip add dns "Ethernet" 1.0.0.1 index=2',
                'netsh interface ip set dns "Wi-Fi" static 1.1.1.1 primary',
                'netsh interface ip add dns "Wi-Fi" 1.0.0.1 index=2',
            ],
        ),
    ],
    "Sistema": [
        (
            "Desactivar telemetría básica",
            "Reduce el envío de datos de diagnóstico de Windows.",
            [
                'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\DataCollection" /v "AllowTelemetry" /t REG_DWORD /d 0 /f',
                "sc stop DiagTrack 2>nul & sc config DiagTrack start= disabled 2>nul",
                "sc stop dmwappushservice 2>nul & sc config dmwappushservice start= disabled 2>nul",
            ],
        ),
        (
            "Prioridad de procesos para juegos",
            "Ajusta Win32PrioritySeparation para favorecer aplicaciones en primer plano.",
            [
                'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\PriorityControl" /v "Win32PrioritySeparation" /t REG_DWORD /d 26 /f',
            ],
        ),
        (
            "Desactivar tips y sugerencias de Windows",
            "Elimina notificaciones y sugerencias molestas del sistema.",
            [
                'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\ContentDeliveryManager" /v "SubscribedContent-338389Enabled" /t REG_DWORD /d 0 /f',
                'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\ContentDeliveryManager" /v "SubscribedContent-310093Enabled" /t REG_DWORD /d 0 /f',
                'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\UserProfileEngagement" /v "ScoobeSystemSettingEnabled" /t REG_DWORD /d 0 /f',
            ],
        ),
    ],
}

TWEAKS_PRO = {
    "Latencia & Input (Fortnite / Shooters)": [
        (
            "Timer Resolution + MMCSS Gaming",
            "Mejora la precisión del timer y prioriza tareas de gaming. Muy importante para input lag.",
            [
                'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile" /v "SystemResponsiveness" /t REG_DWORD /d 0 /f',
                'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile" /v "NetworkThrottlingIndex" /t REG_DWORD /d 4294967295 /f',
                'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile\\Tasks\\Games" /v "GPU Priority" /t REG_DWORD /d 8 /f',
                'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile\\Tasks\\Games" /v "Priority" /t REG_DWORD /d 6 /f',
                'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile\\Tasks\\Games" /v "Scheduling Category" /t REG_SZ /d "High" /f',
                'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile\\Tasks\\Games" /v "SFIO Priority" /t REG_SZ /d "High" /f',
                'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile\\Tasks\\Games" /v "Background Only" /t REG_SZ /d "False" /f',
                'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile\\Tasks\\Games" /v "Clock Rate" /t REG_DWORD /d 10000 /f',
            ],
        ),
        (
            "Network Throttling + TCP optimizado",
            "Desactiva throttling de red y ajusta TCP para mínima latencia.",
            [
                'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile" /v "NetworkThrottlingIndex" /t REG_DWORD /d 4294967295 /f',
                "netsh int tcp set global autotuninglevel=disabled",
                "netsh int tcp set global rss=enabled",
                "netsh int tcp set global ecncapability=disabled",
                'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\Tcpip\\Parameters" /v "TcpAckFrequency" /t REG_DWORD /d 1 /f',
                'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\Tcpip\\Parameters" /v "TCPNoDelay" /t REG_DWORD /d 1 /f',
                'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\Tcpip\\Parameters" /v "TcpDelAckTicks" /t REG_DWORD /d 0 /f',
            ],
        ),
        (
            "Desactivar Nagle Algorithm",
            "Reduce latencia en conexiones TCP (importante en shooters online).",
            [
                'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\Tcpip\\Parameters\\Interfaces" /v "TcpAckFrequency" /t REG_DWORD /d 1 /f',
                'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\Tcpip\\Parameters\\Interfaces" /v "TCPNoDelay" /t REG_DWORD /d 1 /f',
            ],
        ),
        (
            "Prioridad de interrupciones de mouse/teclado",
            "Mejora la respuesta de periféricos de entrada.",
            [
                'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\mouclass\\Parameters" /v "MouseDataQueueSize" /t REG_DWORD /d 20 /f',
                'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\kbdclass\\Parameters" /v "KeyboardDataQueueSize" /t REG_DWORD /d 20 /f',
            ],
        ),
    ],
    "GPU & Gráficos": [
        (
            "GPU Hardware Scheduling + TDR",
            "Activa programación de GPU por hardware y reduce timeouts de driver.",
            [
                'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\GraphicsDrivers" /v "HwSchMode" /t REG_DWORD /d 2 /f',
                'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\GraphicsDrivers" /v "TdrLevel" /t REG_DWORD /d 0 /f',
                'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\GraphicsDrivers" /v "TdrDelay" /t REG_DWORD /d 10 /f',
            ],
        ),
        (
            "Desactivar Game Mode de Windows (recomendado en muchos casos)",
            "En varios sistemas Game Mode genera más problemas que beneficios.",
            [
                'reg add "HKCU\\Software\\Microsoft\\GameBar" /v "AutoGameModeEnabled" /t REG_DWORD /d 0 /f',
                'reg add "HKCU\\Software\\Microsoft\\GameBar" /v "AllowAutoGameMode" /t REG_DWORD /d 0 /f',
            ],
        ),
        (
            "Optimizar prioridad de GPU para juegos",
            "Aumenta la prioridad de la GPU en el programador de tareas.",
            [
                'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile\\Tasks\\Games" /v "GPU Priority" /t REG_DWORD /d 8 /f',
            ],
        ),
    ],
    "Memoria & CPU": [
        (
            "LargeSystemCache + DisablePagingExecutive",
            "Mantiene más código del sistema en RAM (recomendado con 16GB+).",
            [
                'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Memory Management" /v "LargeSystemCache" /t REG_DWORD /d 1 /f',
                'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Memory Management" /v "DisablePagingExecutive" /t REG_DWORD /d 1 /f',
            ],
        ),
        (
            "Desactivar SysMain (Superfetch)",
            "Libera recursos de disco y CPU que Superfetch consume en segundo plano.",
            [
                "sc stop SysMain 2>nul",
                "sc config SysMain start= disabled 2>nul",
            ],
        ),
        (
            "Desactivar Prefetch y Superfetch residual",
            "Complemento para reducir actividad de disco innecesaria.",
            [
                'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Memory Management\\PrefetchParameters" /v "EnablePrefetcher" /t REG_DWORD /d 0 /f',
                'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Memory Management\\PrefetchParameters" /v "EnableSuperfetch" /t REG_DWORD /d 0 /f',
            ],
        ),
        (
            "Ajustar quantum de CPU para gaming",
            "Mejora el scheduling de procesos en primer plano.",
            [
                'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\PriorityControl" /v "Win32PrioritySeparation" /t REG_DWORD /d 26 /f',
            ],
        ),
    ],
    "Fortnite / Competitive Profile": [
        (
            "Perfil Competitivo Fortnite + Shooters",
            "Paquete completo orientado a estabilidad de FPS y mínima latencia.",
            [
                'reg add "HKCU\\System\\GameConfigStore" /v "GameDVR_Enabled" /t REG_DWORD /d 0 /f',
                'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile\\Tasks\\Games" /v "Affinity" /t REG_DWORD /d 0 /f',
                'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile\\Tasks\\Games" /v "Background Only" /t REG_SZ /d "False" /f',
                'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile\\Tasks\\Games" /v "Clock Rate" /t REG_DWORD /d 10000 /f',
                'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile\\Tasks\\Games" /v "GPU Priority" /t REG_DWORD /d 8 /f',
                'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile\\Tasks\\Games" /v "Priority" /t REG_DWORD /d 6 /f',
                'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile\\Tasks\\Games" /v "Scheduling Category" /t REG_SZ /d "High" /f',
                'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile\\Tasks\\Games" /v "SFIO Priority" /t REG_SZ /d "High" /f',
                'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile" /v "SystemResponsiveness" /t REG_DWORD /d 0 /f',
            ],
        ),
    ],
    "Servicios & Mantenimiento": [
        (
            "Crear punto de restauración",
            "Crea un punto de restauración antes de aplicar cambios agresivos.",
            [
                'PowerShell -NoProfile -Command "Checkpoint-Computer -Description \'ZetaBoost Pro\' -RestorePointType \'MODIFY_SETTINGS\' -ErrorAction SilentlyContinue"',
            ],
        ),
        (
            "Pausar Windows Update (30 días)",
            "Evita que Windows Update interrumpa mientras jugás.",
            [
                'PowerShell -NoProfile -Command "$d=(Get-Date).AddDays(30).ToString(\'yyyy-MM-dd\'); New-Item -Path \'HKLM:\\SOFTWARE\\Microsoft\\WindowsUpdate\\UX\\Settings\' -Force | Out-Null; Set-ItemProperty -Path \'HKLM:\\SOFTWARE\\Microsoft\\WindowsUpdate\\UX\\Settings\' -Name \'PauseUpdatesExpiryTime\' -Value $d -ErrorAction SilentlyContinue"',
            ],
        ),
        (
            "Desactivar servicios innecesarios (seguros)",
            "Desactiva servicios que suelen consumir recursos sin beneficio en gaming.",
            [
                "sc config SysMain start= disabled 2>nul",
                "sc config WSearch start= disabled 2>nul",
                "sc config DiagTrack start= disabled 2>nul",
                "sc config dmwappushservice start= disabled 2>nul",
            ],
        ),
    ],
}

# ==================== APP PRINCIPAL ====================
class ZetaBoostApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(f"{APP_NAME}  •  Elite Suite v{APP_VERSION}")
        self.geometry("1140x740")
        self.minsize(1020, 680)
        self.configure(fg_color=COLOR_BG)

        self.pro_activo = False
        self.current_section = "free"

        self._build_ui()
        self._mostrar_free()

        if not es_admin():
            self._log("Se recomiendan permisos de Administrador.")

    def _build_ui(self):
        # ========== SIDEBAR ==========
        sidebar = ctk.CTkFrame(self, width=230, fg_color=COLOR_SIDEBAR, corner_radius=0)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        # Brand
        brand_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        brand_frame.pack(fill="x", pady=(32, 8), padx=20)

        ctk.CTkLabel(
            brand_frame,
            text="ZetaBoost",
            font=("Segoe UI Semibold", 24),
            text_color=COLOR_GREEN,
        ).pack(anchor="w")

        ctk.CTkLabel(
            brand_frame,
            text="Elite Suite",
            font=("Segoe UI", 12),
            text_color=COLOR_TEXT_MUTED,
        ).pack(anchor="w", pady=(0, 4))

        # Estado
        self.lbl_estado = ctk.CTkLabel(
            sidebar,
            text="●  FREE",
            font=("Segoe UI", 12, "bold"),
            text_color=COLOR_TEXT_DIM,
        )
        self.lbl_estado.pack(anchor="w", padx=20, pady=(0, 28))

        # Navegación
        self.nav_buttons = {}
        for key, label in [
            ("free", "Free Tweaks"),
            ("pro", "Pro Tweaks"),
            ("tools", "Herramientas"),
            ("account", "Cuenta"),
        ]:
            btn = ctk.CTkButton(
                sidebar,
                text=label,
                font=("Segoe UI", 14),
                fg_color="transparent",
                hover_color="#141c28",
                text_color=COLOR_TEXT,
                anchor="w",
                height=42,
                corner_radius=8,
                command=lambda k=key: self._navegar(k),
            )
            btn.pack(fill="x", padx=12, pady=2)
            self.nav_buttons[key] = btn

        # Log
        self.status = ctk.CTkTextbox(
            sidebar,
            width=200,
            height=200,
            fg_color="#080c12",
            text_color=COLOR_TEXT_MUTED,
            font=("Consolas", 11),
            corner_radius=10,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        self.status.pack(side="bottom", padx=14, pady=18, fill="x")
        self._log("Listo.")

        # ========== CONTENIDO ==========
        self.content = ctk.CTkFrame(self, fg_color=COLOR_BG, corner_radius=0)
        self.content.pack(side="left", fill="both", expand=True)

        # Header
        header = ctk.CTkFrame(self.content, fg_color="transparent", height=70)
        header.pack(fill="x", padx=32, pady=(24, 8))

        self.lbl_titulo = ctk.CTkLabel(
            header,
            text="Free Tweaks",
            font=("Segoe UI Semibold", 22),
            text_color=COLOR_TEXT,
        )
        self.lbl_titulo.pack(side="left")

        self.lbl_subtitulo = ctk.CTkLabel(
            header,
            text="Optimizaciones seguras y recomendadas",
            font=("Segoe UI", 13),
            text_color=COLOR_TEXT_MUTED,
        )
        self.lbl_subtitulo.pack(side="left", padx=(16, 0), pady=(4, 0))

        # Scroll area
        self.scroll = ctk.CTkScrollableFrame(
            self.content,
            fg_color="transparent",
            corner_radius=0,
            scrollbar_button_color=COLOR_BORDER,
            scrollbar_button_hover_color=COLOR_GREEN_DIM,
        )
        self.scroll.pack(fill="both", expand=True, padx=24, pady=(0, 24))

    def _navegar(self, section: str):
        self.current_section = section
        for k, btn in self.nav_buttons.items():
            btn.configure(fg_color="transparent", text_color=COLOR_TEXT)

        self.nav_buttons[section].configure(fg_color="#141c28", text_color=COLOR_GREEN)

        if section == "free":
            self._mostrar_free()
        elif section == "pro":
            self._mostrar_pro()
        elif section == "tools":
            self._mostrar_tools()
        elif section == "account":
            self._mostrar_account()

    def _log(self, msg: str):
        timestamp = time.strftime("%H:%M")
        self.status.insert("end", f"[{timestamp}] {msg}\n")
        self.status.see("end")

    def _limpiar_scroll(self):
        for w in self.scroll.winfo_children():
            w.destroy()

    def _cargar_tweaks(self, catalogo: dict, pro: bool = False):
        self._limpiar_scroll()

        if pro and not self.pro_activo:
            lock = ctk.CTkFrame(self.scroll, fg_color=COLOR_CARD, corner_radius=14)
            lock.pack(fill="x", pady=40, padx=20)

            ctk.CTkLabel(
                lock,
                text="Contenido Pro",
                font=("Segoe UI Semibold", 20),
                text_color=COLOR_GREEN,
            ).pack(pady=(36, 8))

            ctk.CTkLabel(
                lock,
                text="Activá tu licencia Pro para desbloquear\ntweaks avanzados de latencia, GPU y rendimiento.",
                font=("Segoe UI", 14),
                text_color=COLOR_TEXT_MUTED,
                justify="center",
            ).pack(pady=(0, 28))
            return

        for categoria, items in catalogo.items():
            cat_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
            cat_frame.pack(fill="x", pady=(18, 6), padx=6)

            ctk.CTkLabel(
                cat_frame,
                text=categoria,
                font=("Segoe UI Semibold", 14),
                text_color=COLOR_GREEN,
            ).pack(anchor="w")

            for nombre, descripcion, comandos in items:
                card = ctk.CTkFrame(
                    self.scroll,
                    fg_color=COLOR_CARD,
                    corner_radius=12,
                    border_width=1,
                    border_color=COLOR_BORDER,
                )
                card.pack(fill="x", pady=5, padx=4)

                inner = ctk.CTkFrame(card, fg_color="transparent")
                inner.pack(fill="x", padx=18, pady=14)

                left = ctk.CTkFrame(inner, fg_color="transparent")
                left.pack(side="left", fill="both", expand=True)

                ctk.CTkLabel(
                    left,
                    text=nombre,
                    font=("Segoe UI Semibold", 14),
                    text_color=COLOR_TEXT,
                    anchor="w",
                ).pack(anchor="w")

                ctk.CTkLabel(
                    left,
                    text=descripcion,
                    font=("Segoe UI", 12),
                    text_color=COLOR_TEXT_MUTED,
                    anchor="w",
                    wraplength=640,
                ).pack(anchor="w", pady=(3, 0))

                btn = ctk.CTkButton(
                    inner,
                    text="Aplicar",
                    width=96,
                    height=34,
                    font=("Segoe UI", 13),
                    fg_color=COLOR_GREEN,
                    hover_color=COLOR_GREEN_HOVER,
                    text_color="#03150c",
                    corner_radius=8,
                    command=lambda n=nombre, c=comandos: self._aplicar(n, c),
                )
                btn.pack(side="right", padx=(16, 0))

    def _aplicar(self, nombre: str, comandos: list):
        self._log(f"Aplicando: {nombre}")

        def job():
            ok = sum(1 for cmd in comandos if correr(cmd))
            total = len(comandos)
            if ok == total:
                self._log(f"OK  {nombre}  ({ok}/{total})")
            elif ok > 0:
                self._log(f"Parcial  {nombre}  ({ok}/{total})")
            else:
                self._log(f"Error  {nombre}")

        threading.Thread(target=job, daemon=True).start()

    def _mostrar_free(self):
        self.lbl_titulo.configure(text="Free Tweaks")
        self.lbl_subtitulo.configure(text="Optimizaciones seguras y recomendadas")
        self._cargar_tweaks(TWEAKS_FREE, pro=False)
        self.nav_buttons["free"].configure(fg_color="#141c28", text_color=COLOR_GREEN)

    def _mostrar_pro(self):
        self.lbl_titulo.configure(text="Pro Tweaks")
        self.lbl_subtitulo.configure(text="Latencia extrema • Fortnite & Competitive")
        self._cargar_tweaks(TWEAKS_PRO, pro=True)

    def _mostrar_tools(self):
        self.lbl_titulo.configure(text="Herramientas")
        self.lbl_subtitulo.configure(text="Diagnóstico y utilidades")
        self._limpiar_scroll()

        card = ctk.CTkFrame(self.scroll, fg_color=COLOR_CARD, corner_radius=14, border_width=1, border_color=COLOR_BORDER)
        card.pack(fill="x", pady=12, padx=6)

        ctk.CTkLabel(
            card,
            text="Diagnóstico del sistema",
            font=("Segoe UI Semibold", 16),
            text_color=COLOR_TEXT,
        ).pack(anchor="w", padx=22, pady=(20, 6))

        ctk.CTkLabel(
            card,
            text="Revisa uso de RAM, CPU y GPU detectada.",
            font=("Segoe UI", 13),
            text_color=COLOR_TEXT_MUTED,
        ).pack(anchor="w", padx=22, pady=(0, 14))

        ctk.CTkButton(
            card,
            text="Ejecutar diagnóstico",
            width=170,
            height=36,
            font=("Segoe UI", 13),
            fg_color=COLOR_GREEN,
            hover_color=COLOR_GREEN_HOVER,
            text_color="#03150c",
            corner_radius=8,
            command=self._diagnostico,
        ).pack(anchor="w", padx=22, pady=(0, 22))

        rec = ctk.CTkFrame(self.scroll, fg_color=COLOR_CARD, corner_radius=14, border_width=1, border_color=COLOR_BORDER)
        rec.pack(fill="x", pady=12, padx=6)

        ctk.CTkLabel(
            rec,
            text="Recomendación de uso",
            font=("Segoe UI Semibold", 15),
            text_color=COLOR_GREEN,
        ).pack(anchor="w", padx=22, pady=(20, 10))

        ctk.CTkLabel(
            rec,
            text="Para Fortnite y shooters competitivos:\n\n1. Aplicá todos los Free Tweaks\n2. Activá Pro y aplicá Latencia & Input + Perfil Competitivo\n3. Reiniciá el PC después de los cambios de red y MMCSS\n4. Verificá que tu monitor esté en la tasa de refresco máxima",
            font=("Segoe UI", 13),
            text_color=COLOR_TEXT_MUTED,
            justify="left",
        ).pack(anchor="w", padx=22, pady=(0, 22))

    def _mostrar_account(self):
        self.lbl_titulo.configure(text="Cuenta")
        self.lbl_subtitulo.configure(text="Licencia y estado")
        self._limpiar_scroll()

        card = ctk.CTkFrame(self.scroll, fg_color=COLOR_CARD, corner_radius=14, border_width=1, border_color=COLOR_BORDER)
        card.pack(fill="x", pady=30, padx=20)

        estado = "PRO ACTIVO" if self.pro_activo else "FREE"
        color = COLOR_GREEN if self.pro_activo else COLOR_TEXT_MUTED

        ctk.CTkLabel(
            card,
            text=f"Estado actual:  {estado}",
            font=("Segoe UI Semibold", 18),
            text_color=color,
        ).pack(pady=(36, 12))

        ctk.CTkLabel(
            card,
            text="La activación Pro se conectará cuando\ntengas el sistema de pagos listo en la web.",
            font=("Segoe UI", 14),
            text_color=COLOR_TEXT_MUTED,
            justify="center",
        ).pack(pady=(0, 36))

    def _diagnostico(self):
        self._log("Ejecutando diagnóstico...")

        def job():
            try:
                mem = psutil.virtual_memory()
                self._log(f"RAM: {mem.percent}%  ({mem.used // (1024**3)}/{mem.total // (1024**3)} GB)")
                self._log(f"CPU: {psutil.cpu_percent(interval=0.8)}%")

                try:
                    out = subprocess.check_output(
                        'wmic path win32_VideoController get name',
                        shell=True,
                        creationflags=subprocess.CREATE_NO_WINDOW,
                    ).decode(errors="ignore")
                    for line in out.splitlines():
                        if line.strip() and "Name" not in line:
                            self._log(f"GPU: {line.strip()}")
                            break
                except Exception:
                    pass

                self._log("Diagnóstico terminado.")
            except Exception as e:
                self._log(f"Error: {e}")

        threading.Thread(target=job, daemon=True).start()


# ==================== MAIN ====================
if __name__ == "__main__":
    if not es_admin():
        try:
            relanzar_como_admin()
        except Exception:
            pass

    app = ZetaBoostApp()
    app.mainloop()
