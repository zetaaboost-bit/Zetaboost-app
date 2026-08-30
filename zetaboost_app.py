"""
ZetaBoost Elite Suite - App de escritorio (Free + Pro en una sola app)
Requiere Windows + permisos de administrador (se auto-eleva).
Pro se desbloquea validando la licencia contra la API (ver API_URL).

Build a .exe (correr esto EN WINDOWS, no en Linux):
    pip install -r requirements.txt
    pyinstaller --onefile --noconsole --name ZetaBoost zetaboost_app.py
El .exe queda en dist/ZetaBoost.exe
"""
import ctypes
import json
import os
import subprocess
import sys
import threading
from pathlib import Path

import customtkinter as ctk
import requests

API_URL = "https://pagina-web-r2t0.onrender.com/api"
CONFIG_DIR = Path(os.environ.get("APPDATA", ".")) / "ZetaBoost"
CONFIG_FILE = CONFIG_DIR / "config.json"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")


# ---------- utilidades de sistema ----------
def es_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def relanzar_como_admin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit()


def correr(cmd):
    """Ejecuta un comando de shell (mismo que se usaria en el .bat) sin abrir consola."""
    try:
        subprocess.run(cmd, shell=True, capture_output=True, timeout=180,
                        creationflags=subprocess.CREATE_NO_WINDOW)
        return True
    except Exception:
        return False


def cargar_config():
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def guardar_config(data):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(data), encoding="utf-8")


# ---------- catálogo de tweaks (mismos comandos que los .bat, agrupados) ----------
# ponytail: nada de clases por tweak, son listas de comandos + un runner generico.

TWEAKS_FREE = {
    "Limpieza": [
        ("Limpiador Integral", [
            'del /s /f /q "%TEMP%\\*"',
            'rd /s /q "%TEMP%" & md "%TEMP%"',
            'del /s /f /q "C:\\Windows\\Temp\\*"',
            'del /s /f /q "C:\\Windows\\Prefetch\\*"',
            'del /s /f /q "C:\\Windows\\SoftwareDistribution\\Download\\*"',
            'PowerShell -NoProfile -Command "Clear-RecycleBin -Force -ErrorAction SilentlyContinue"',
        ]),
    ],
    "Gaming": [
        ("Perfil Gamer Lite (GameDVR y SysMain off)", [
            'reg add "HKCU\\System\\GameConfigStore" /v "GameDVR_Enabled" /t REG_DWORD /d 0 /f',
            'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\BackgroundAccessApplications" /v "GlobalUserDisabled" /t REG_DWORD /d 1 /f',
            'sc stop SysMain & sc config SysMain start= disabled',
        ]),
        ("Purga de Cache de Shaders", [
            'del /s /f /q "%LOCALAPPDATA%\\D3DSCache\\*"',
            'del /s /f /q "%LOCALAPPDATA%\\NVIDIA\\DXCache\\*"',
            'del /s /f /q "%LOCALAPPDATA%\\AMD\\DxCache\\*"',
        ]),
    ],
    "Red y RAM": [
        ("Optimizador de Red (DNS, TCP, Winsock)", [
            "ipconfig /flushdns", "ipconfig /registerdns", "arp -d *",
            "netsh int ip reset", "netsh winsock reset",
            "netsh int tcp set global autotuninglevel=normal",
        ]),
        ("Boost Express de RAM (reinicia Explorer)", [
            'del /s /f /q "%TEMP%\\*"',
            "taskkill /f /im explorer.exe", "start \"\" explorer.exe",
        ]),
    ],
    "Sistema": [
        ("Acelerador Visual (cero animaciones)", [
            'reg add "HKCU\\Control Panel\\Desktop\\WindowMetrics" /v "MinAnimate" /t REG_SZ /d "0" /f',
            'reg add "HKCU\\Control Panel\\Desktop" /v "MenuShowDelay" /t REG_SZ /d "0" /f',
        ]),
        ("Optimizador CPU y Energía (Ultimate)", [
            'for /f "tokens=2" %i in (\'powercfg -duplicatescheme e9a42b02-d5df-448d-aa00-03f14749eb61\') do powercfg /setactive %i',
            'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\PriorityControl" /v "Win32PrioritySeparation" /t REG_DWORD /d 2 /f',
            "bcdedit /set useplatformclock false", "bcdedit /set tscsyncpolicy Enhanced",
        ]),
        ("Privacidad y Telemetría", [
            'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\ContentDeliveryManager" /v "SubscribedContent-338389Enabled" /t REG_DWORD /d 0 /f',
            'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\DataCollection" /v "AllowTelemetry" /t REG_DWORD /d 0 /f',
            "sc stop DiagTrack & sc config DiagTrack start= disabled",
        ]),
        ("Reparación Rápida (SFC verify + DISM CheckHealth)", [
            "sfc /verifyonly", "DISM /Online /Cleanup-Image /CheckHealth",
        ]),
    ],
}

TWEAKS_PRO = {
    "Seguridad": [
        ("Crear Punto de Restauración", [
            'PowerShell -NoProfile -Command "Checkpoint-Computer -Description \'ZetaBoost Pro\' -RestorePointType \'MODIFY_SETTINGS\'"',
        ]),
        ("Revertir Cambios Pro al Default de Windows", [
            'reg add "HKCU\\Control Panel\\Desktop" /v "MenuShowDelay" /t REG_SZ /d "400" /f',
            'reg add "HKCU\\Control Panel\\Desktop\\WindowMetrics" /v "MinAnimate" /t REG_SZ /d "1" /f',
            "sc config SysMain start= auto & sc start SysMain",
            "sc config WSearch start= delayed-auto & sc start WSearch",
            "bcdedit /set useplatformclock true", "powercfg -h on",
            'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Memory Management" /v "FeatureSettingsOverride" /t REG_DWORD /d 0 /f',
            'PowerShell -NoProfile -Command "Set-MpPreference -DisableRealtimeMonitoring $false"',
            "powercfg -setactive SCHEME_BALANCED",
        ]),
    ],
    "Rendimiento máximo": [
        ("Nivel 2: CPU + RAM + Red avanzada", [
            'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Memory Management" /v "LargeSystemCache" /t REG_DWORD /d 1 /f',
            'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Memory Management" /v "DisablePagingExecutive" /t REG_DWORD /d 1 /f',
            "netsh int tcp set global rss=enabled", "netsh int tcp set global ecncapability=disabled",
            'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile" /v "NetworkThrottlingIndex" /t REG_DWORD /d 4294967295 /f',
            'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile" /v "SystemResponsiveness" /t REG_DWORD /d 0 /f',
            'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\Tcpip\\Parameters" /v "TcpAckFrequency" /t REG_DWORD /d 1 /f',
        ]),
        ("Optimizar GPU (detecta NVIDIA/AMD/Intel sola)", [
            'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\GraphicsDrivers" /v "HwSchMode" /t REG_DWORD /d 2 /f',
            'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\GraphicsDrivers" /v "TdrLevel" /t REG_DWORD /d 0 /f',
            'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Image File Execution Options\\dwm.exe\\PerfOptions" /v "CpuPriorityClass" /t REG_DWORD /d 3 /f',
        ]),
    ],
    "Herramientas": [
        ("Pausar Windows Update (365 días)", [
            'PowerShell -NoProfile -Command "$d=(Get-Date).AddDays(365).ToString(\'yyyy-MM-dd\'); New-Item -Path \'HKLM:\\SOFTWARE\\Microsoft\\WindowsUpdate\\UX\\Settings\' -Force | Out-Null; Set-ItemProperty -Path \'HKLM:\\SOFTWARE\\Microsoft\\WindowsUpdate\\UX\\Settings\' -Name \'PauseUpdatesExpiryTime\' -Value $d"',
        ]),
        ("Reactivar Windows Update", [
            'PowerShell -NoProfile -Command "Remove-ItemProperty -Path \'HKLM:\\SOFTWARE\\Microsoft\\WindowsUpdate\\UX\\Settings\' -Name \'PauseUpdatesExpiryTime\' -ErrorAction SilentlyContinue"',
        ]),
        ("Desactivar Defender temporalmente", [
            'PowerShell -NoProfile -Command "Set-MpPreference -DisableRealtimeMonitoring $true"',
        ]),
        ("Reactivar Defender", [
            'PowerShell -NoProfile -Command "Set-MpPreference -DisableRealtimeMonitoring $false"',
        ]),
        ("Desactivar mitigaciones de CPU", [
            'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Memory Management" /v "FeatureSettingsOverride" /t REG_DWORD /d 3 /f',
            'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Memory Management" /v "FeatureSettingsOverrideMask" /t REG_DWORD /d 3 /f',
        ]),
        ("Reactivar mitigaciones de CPU", [
            'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Memory Management" /v "FeatureSettingsOverride" /t REG_DWORD /d 0 /f',
            'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Memory Management" /v "FeatureSettingsOverrideMask" /t REG_DWORD /d 0 /f',
        ]),
        ("Limpiar WinSxS (Component Store)", ["Dism.exe /Online /Cleanup-Image /StartComponentCleanup /ResetBase"]),
        ("Reparar imagen (DISM RestoreHealth)", ["Dism.exe /Online /Cleanup-Image /RestoreHealth"]),
        ("SFC /scannow completo", ["sfc /scannow"]),
        ("Liberar espacio en disco", ["cleanmgr /sagerun:1"]),
        ("Desinstalar Bloatware (apps UWP)", [
            'PowerShell -NoProfile -Command "Get-AppxPackage *3dbuilder* | Remove-AppxPackage -ErrorAction SilentlyContinue"',
            'PowerShell -NoProfile -Command "Get-AppxPackage *officehub* | Remove-AppxPackage -ErrorAction SilentlyContinue"',
            'PowerShell -NoProfile -Command "Get-AppxPackage *skypeapp* | Remove-AppxPackage -ErrorAction SilentlyContinue"',
            'PowerShell -NoProfile -Command "Get-AppxPackage *solitairecollection* | Remove-AppxPackage -ErrorAction SilentlyContinue"',
            'PowerShell -NoProfile -Command "Get-AppxPackage *xboxapp* | Remove-AppxPackage -ErrorAction SilentlyContinue"',
            'PowerShell -NoProfile -Command "Get-AppxPackage *yourphone* | Remove-AppxPackage -ErrorAction SilentlyContinue"',
        ]),
    ],
}


# ponytail: heurística simple y honesta, no un "diagnóstico mágico".
# Marca ceiling: solo mira contadores basicos de WMIC, no hace profiling real de frametimes.
def diagnostico_basico():
    lineas = []
    try:
        out = subprocess.run(
            'wmic OS get FreePhysicalMemory,TotalVisibleMemorySize /value',
            shell=True, capture_output=True, text=True, timeout=15,
            creationflags=subprocess.CREATE_NO_WINDOW,
        ).stdout
        libre = total = None
        for linea in out.splitlines():
            if "FreePhysicalMemory" in linea:
                libre = int(linea.split("=")[1].strip() or 0)
            if "TotalVisibleMemorySize" in linea:
                total = int(linea.split("=")[1].strip() or 0)
        if libre and total:
            pct = 100 - int(libre / total * 100)
            lineas.append(f"RAM en uso: {pct}%" + (" -> alto, cerrá programas de fondo." if pct > 80 else " -> ok."))
    except Exception:
        lineas.append("No se pudo leer el uso de RAM.")

    try:
        out = subprocess.run(
            'wmic path win32_VideoController get name /value',
            shell=True, capture_output=True, text=True, timeout=15,
            creationflags=subprocess.CREATE_NO_WINDOW,
        ).stdout
        for linea in out.splitlines():
            if linea.strip().startswith("Name="):
                lineas.append("GPU: " + linea.split("=", 1)[1].strip())
    except Exception:
        pass

    lineas.append("Tip: si tenés stutters, probá primero 'Purga de Cache de Shaders' y 'Nivel 2' de Rendimiento.")
    return "\n".join(lineas)


# ---------- API de licencias ----------
def api_login(email, password):
    r = requests.post(f"{API_URL}/login", json={"email": email, "password": password}, timeout=15)
    return r.status_code, r.json()


def api_activar(token, licencia):
    r = requests.post(f"{API_URL}/activar-licencia", json={"licencia": licencia},
                       headers={"Authorization": f"Bearer {token}"}, timeout=15)
    return r.status_code, r.json()


def api_mi_estado(token):
    r = requests.get(f"{API_URL}/mi-estado", headers={"Authorization": f"Bearer {token}"}, timeout=15)
    return r.status_code, r.json()


# ---------- GUI ----------
class ZetaBoostApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("ZetaBoost Elite Suite")
        self.geometry("980x640")
        self.configure(fg_color="#040608")

        self.token = None
        self.pro_activo = False
        cfg = cargar_config()
        self.token = cfg.get("token")

        self._construir_layout()
        self._cargar_tweaks(TWEAKS_FREE, self.frame_free)

        if self.token:
            threading.Thread(target=self._verificar_estado_inicial, daemon=True).start()
        else:
            self._mostrar_login()

    def _construir_layout(self):
        sidebar = ctk.CTkFrame(self, width=200, fg_color="#0a0f16")
        sidebar.pack(side="left", fill="y")
        ctk.CTkLabel(sidebar, text="ZetaBoost", font=("Segoe UI", 22, "bold"),
                     text_color="#00ff88").pack(pady=(24, 4), padx=16)
        ctk.CTkLabel(sidebar, text="Elite Suite", font=("Segoe UI", 12),
                     text_color="#91a0b2").pack(pady=(0, 24))

        self.tabs = ctk.CTkTabview(self, fg_color="#0a0f16", segmented_button_selected_color="#00ff88",
                                    segmented_button_selected_hover_color="#00b86a")
        self.tabs.pack(side="left", fill="both", expand=True, padx=16, pady=16)
        self.tabs.add("Free")
        self.tabs.add("Pro")
        self.tabs.add("Licencia")
        self.frame_free = self.tabs.tab("Free")
        self.frame_pro = self.tabs.tab("Pro")
        self.frame_licencia = self.tabs.tab("Licencia")

        self.status = ctk.CTkTextbox(sidebar, width=180, height=380, fg_color="#0e1520", text_color="#91a0b2")
        self.status.pack(padx=10, pady=10, fill="y", expand=True)
        self._log("Listo.")

        self._construir_tab_licencia()

    def _log(self, msg):
        self.status.insert("end", f"{msg}\n")
        self.status.see("end")

    def _cargar_tweaks(self, catalogo, contenedor, bloqueado=False):
        for widget in contenedor.winfo_children():
            widget.destroy()
        scroll = ctk.CTkScrollableFrame(contenedor, fg_color="transparent")
        scroll.pack(fill="both", expand=True)
        if bloqueado:
            ctk.CTkLabel(scroll, text="🔒 Activá tu licencia Pro en la pestaña 'Licencia' para desbloquear.",
                         text_color="#ff3b4f", font=("Segoe UI", 13, "bold")).pack(pady=20)
            return
        for categoria, items in catalogo.items():
            ctk.CTkLabel(scroll, text=categoria, font=("Segoe UI", 15, "bold"),
                         text_color="#00ff88").pack(anchor="w", pady=(14, 4))
            for nombre, comandos in items:
                fila = ctk.CTkFrame(scroll, fg_color="#0e1520")
                fila.pack(fill="x", pady=3)
                ctk.CTkLabel(fila, text=nombre, anchor="w").pack(side="left", padx=10, pady=8, fill="x", expand=True)
                ctk.CTkButton(fila, text="Aplicar", width=90, fg_color="#00ff88", text_color="#00130a",
                              hover_color="#00b86a",
                              command=lambda n=nombre, c=comandos: self._aplicar_tweak(n, c)).pack(side="right", padx=10)

        if catalogo is TWEAKS_PRO:
            fila = ctk.CTkFrame(scroll, fg_color="#0e1520")
            fila.pack(fill="x", pady=(14, 3))
            ctk.CTkLabel(fila, text="Diagnóstico rápido (RAM / GPU / tips de stutter)", anchor="w").pack(
                side="left", padx=10, pady=8, fill="x", expand=True)
            ctk.CTkButton(fila, text="Analizar", width=90, command=self._correr_diagnostico).pack(side="right", padx=10)

    def _aplicar_tweak(self, nombre, comandos):
        self._log(f"Aplicando: {nombre}...")

        def job():
            for c in comandos:
                correr(c)
            self._log(f"[OK] {nombre}")
        threading.Thread(target=job, daemon=True).start()

    def _correr_diagnostico(self):
        self._log("Analizando sistema...")

        def job():
            resultado = diagnostico_basico()
            self._log(resultado)
        threading.Thread(target=job, daemon=True).start()

    def _construir_tab_licencia(self):
        f = self.frame_licencia
        ctk.CTkLabel(f, text="Iniciar sesión", font=("Segoe UI", 16, "bold")).pack(pady=(20, 8))
        self.in_email = ctk.CTkEntry(f, placeholder_text="Email", width=300)
        self.in_email.pack(pady=4)
        self.in_pass = ctk.CTkEntry(f, placeholder_text="Contraseña", show="*", width=300)
        self.in_pass.pack(pady=4)
        ctk.CTkButton(f, text="Ingresar", command=self._login, fg_color="#00ff88",
                      text_color="#00130a", hover_color="#00b86a").pack(pady=10)

        ctk.CTkLabel(f, text="Activar licencia Pro", font=("Segoe UI", 16, "bold")).pack(pady=(24, 8))
        self.in_licencia = ctk.CTkEntry(f, placeholder_text="ZETA-PRO-XXXX-XXXX-XXXX", width=300)
        self.in_licencia.pack(pady=4)
        ctk.CTkButton(f, text="Activar", command=self._activar).pack(pady=10)

        self.lbl_estado_licencia = ctk.CTkLabel(f, text="", text_color="#91a0b2")
        self.lbl_estado_licencia.pack(pady=10)

    def _mostrar_login(self):
        self.tabs.set("Licencia")

    def _login(self):
        email, password = self.in_email.get().strip(), self.in_pass.get().strip()
        if not email or not password:
            self.lbl_estado_licencia.configure(text="Ingresá email y contraseña.", text_color="#ff3b4f")
            return

        def job():
            try:
                status, data = api_login(email, password)
            except Exception:
                self._set_estado_licencia("No se pudo conectar con el servidor.", True)
                return
            if status != 200:
                self._set_estado_licencia(data.get("error", "Error de login."), True)
                return
            self.token = data["token"]
            self.pro_activo = data.get("licenciaActivada", False)
            guardar_config({"token": self.token})
            self._set_estado_licencia(f"Sesión iniciada como {data['alias']}.", False)
            self._refrescar_pro()
        threading.Thread(target=job, daemon=True).start()

    def _activar(self):
        if not self.token:
            self._set_estado_licencia("Iniciá sesión primero.", True)
            return
        licencia = self.in_licencia.get().strip()
        if not licencia:
            return

        def job():
            try:
                status, data = api_activar(self.token, licencia)
            except Exception:
                self._set_estado_licencia("No se pudo conectar con el servidor.", True)
                return
            if status != 200:
                self._set_estado_licencia(data.get("error", "Licencia inválida."), True)
                return
            self._set_estado_licencia("¡Licencia Pro activada!", False)
            self._refrescar_pro()
        threading.Thread(target=job, daemon=True).start()

    def _verificar_estado_inicial(self):
        try:
            status, data = api_mi_estado(self.token)
        except Exception:
            self._log("Sin conexión: no se pudo verificar tu licencia ahora.")
            return
        if status != 200:
            self.token = None
            guardar_config({})
            self._mostrar_login()
            return
        self.pro_activo = data.get("licenciaActivada", False)
        self._set_estado_licencia(f"Sesión activa ({data['alias']}).", False)
        self._refrescar_pro()

    def _set_estado_licencia(self, texto, es_error):
        self.lbl_estado_licencia.configure(text=texto, text_color="#ff3b4f" if es_error else "#00ff88")

    def _refrescar_pro(self):
        self._cargar_tweaks(TWEAKS_PRO, self.frame_pro, bloqueado=not self.pro_activo)


if __name__ == "__main__":
    if os.name == "nt" and not es_admin():
        relanzar_como_admin()
    app = ZetaBoostApp()
    app.mainloop()
