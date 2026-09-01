# ZetaBoost

**Precision optimization for Windows** — modern, safe, fully reversible.

ZetaBoost is a Windows PC optimization suite with a modular architecture, a sidebar-driven
modern dark UI, real registry / power / services / cleaning actions, and a full **FREE / PRO**
tier system. Every optimization is logged and can be rolled back.

> No fake features. No irreversible defaults. No fake "RAM boosters".
> When something cannot be implemented safely yet, ZetaBoost tells you: `NOT IMPLEMENTED YET`.

---

## Stack & why

- **Python 3.10+** — direct access to Windows APIs (`winreg`, `wmi`, `psutil`, `ctypes`, `powershell`, `netsh`, `sc`, `powercfg`, `dism`, `sfc`).
- **PySide6 (Qt 6)** — modern native UI, custom QSS theme, hardware-accelerated widgets.
- **Modular architecture** — every module is independent; adding a tweak or module doesn't require rewriting others.
- Compiles to a single `.exe` with **PyInstaller**.

---

## Project structure

```
ZetaBoost/
├── main.py                        # Entry point
├── requirements.txt
├── README.md
├── app/
│   ├── core/                      # constants, config, logger, license, admin, theme
│   ├── hardware/                  # detector, live monitor
│   ├── optimization/              # engine + tweak database (modular)
│   ├── gaming/                    # gaming_mode, profiles, live_boost
│   ├── cleaner/                   # cleaner
│   ├── network/                   # network
│   ├── services/                  # services_manager
│   ├── startup/                   # startup_manager
│   ├── privacy/                   # privacy
│   ├── power/                     # power plans
│   ├── repair/                    # dism / sfc / windows update
│   ├── storage/                   # trim / defrag / drive health
│   ├── memory/                    # memory report + working set trim
│   ├── backup/                    # session backups + restore point
│   ├── diagnostics/               # report generator
│   └── ui/
│       ├── main_window.py         # sidebar + stacked pages
│       ├── sidebar.py
│       ├── widgets/               # cards, gauges, metric bars
│       └── pages/                 # one file per screen (home, my_pc, boost, ...)
├── config/         # settings.json, license.json
├── tweaks/         # (reserved for user-added tweak JSON packs)
├── profiles/       # game profiles + gaming mode state
├── backups/        # session_*.json snapshots
├── logs/           # session logs + diagnostic reports
└── assets/         # icon.png etc.
```

---

## Installation & Run

Requires **Python 3.10 or 3.11** on Windows 10/11.

```powershell
cd ZetaBoost
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Some optimizations (services, HKLM registry, DISM/SFC, restore points) require **Administrator**
privileges. Right-click your terminal → *Run as administrator*, or the app will prompt you.

---

## Building the .exe (PyInstaller)

```powershell
pip install pyinstaller
pyinstaller --noconfirm --windowed --name ZetaBoost ^
    --icon assets\icon.ico ^
    --collect-submodules PySide6 ^
    --collect-submodules wmi ^
    main.py
```

The result appears in `dist/ZetaBoost/ZetaBoost.exe`. Ship the whole `dist/ZetaBoost/` folder
(or use `--onefile` for a single-file build).

---

## FREE features (implemented)

- System Information & My PC (CPU / GPU / RAM / storage / Windows)
- Basic System Scan + System Score (real, computed from live metrics)
- Live Monitor (CPU, RAM, disk I/O, network)
- Temporary Cleaner (%TEMP%, %TMP%, C:\Windows\Temp)
- Recycle Bin Cleaner
- Thumbnail cache cleaner
- Basic Shader Cache cleaner (NVIDIA / AMD / D3DSCache)
- Basic Gaming Mode (enable/disable, reversible)
- GameDVR / Game Bar controls
- Basic Network Tools (ping, flush DNS, Winsock reset, TCP/IP reset, adapter/DNS view)
- Basic RAM info + safe working-set trim (no fake boosters)
- Basic Startup info (view + toggle HKCU entries)
- Basic Windows tweaks (visual effects → performance)
- Basic privacy tweaks (advertising ID, telemetry min)
- Basic power plan viewer

## PRO features (implemented)

- Deep Cleaner: Windows Update cache, Delivery Optimization cache
- HAGS (Hardware-Accelerated GPU Scheduling) toggle
- Ultimate Performance power plan creation
- Advanced network tweak: Disable Nagle's algorithm (per-interface)
- Live Boost: auto-apply game profile when process detected, auto-restore on exit
- Full Services Manager (categorized: Telemetry / Xbox / Print / Remote / Bluetooth / Location / Indexing / Optional / Gaming)
- Full Startup Manager
- Repair Center: DISM CheckHealth / RestoreHealth, SFC /scannow, WU cache reset
- Storage optimizer: TRIM (SSD/NVMe) / Defrag (HDD)
- Backup / Restore Center with per-session snapshots + restore last session
- Windows System Restore Point creation
- Diagnostics report (.json + .txt) exportable
- Game Profiles (Fortnite / VALORANT / CS2 / Minecraft / Roblox / General Gaming + custom)

## NOT IMPLEMENTED YET (roadmap)

- SMART / drive-health granular metrics
- NVIDIA NVML & AMD ADL native GPU telemetry (temp / util)
- Windows Debloat catalog UI (safe removal of AppX bundles)
- Real license server (online activation, subscription, expiration checks)
- User account / Emergent-style login
- Automatic scheduled maintenance
- Per-vendor GPU control panels beyond HAGS
- CPU temperature on Windows without third-party bridge (OpenHardwareMonitor / LibreHardwareMonitor)

---

## Architecture principles

1. **Tweak database is modular** (`app/optimization/tweak_database.py`).
   Adding a tweak = adding one `Tweak(...)` object in `load_builtin_tweaks()`.
   Each tweak carries: id, name, category, description, risk, tier, supported OS/vendors,
   `apply_fn`, `restore_fn`, `status_fn`. No other file changes needed.

2. **The engine (`optimization/engine.py`) is the only path that applies changes.**
   Flow: *compatibility check → snapshot → apply → verify → structured log*.

3. **Backups are automatic per session.** Every change gets a snapshot in `backups/session_*.json`.
   The Backups page can restore everything from the last session.

4. **License architecture is ready for real activation.** Today it's a local JSON toggle
   (`config/license.json`) but the `LicenseManager` API already exposes `activate_mock_pro`,
   `revoke`, `require_pro`, `hwid`, `expires_at`, `key`, `email` — ready to be wired to a
   real activation server.

5. **The app is a real app, not a script**. UI, engine, hardware, gaming, cleaner, backup,
   diagnostics are separate packages. Nothing is duplicated across the code.

6. **Safety first.** Critical services (Defender, Firewall, Windows Update, RPC, etc.) are
   in a hardcoded protected set (`app/services/services_manager.py::CRITICAL_SERVICES`) and
   cannot be disabled through the UI. Every tweak has a `restore_fn`.

---

## Logs

- Session logs → `logs/YYYY-MM-DD_HHMMSS_session.log`
- Diagnostic reports → `logs/diagnostic_*.json` + `logs/diagnostic_*.txt`
- Structured action lines look like:
  `module=gaming.gamedvr_off | action=apply | result=OK | prev=1 | new=0`

---

## First run

1. Launch `python main.py` (or `ZetaBoost.exe`).
2. The app opens on **Home**. You'll see the System Score and live metrics update in real time.
3. Go to **Boost** and click **SCAN MY PC** to see recommendations. Review, uncheck what you
   don't want, and press **APPLY RECOMMENDED**.
4. Anything you don't like → **Backups → RESTORE LAST SESSION**.
5. To try the PRO experience locally, go to **Settings → License → Activate as PRO**, then
   restart ZetaBoost. This is a local mock; no online activation is performed.

---

## License

Personal / educational use. You own the code you generated with this template.
