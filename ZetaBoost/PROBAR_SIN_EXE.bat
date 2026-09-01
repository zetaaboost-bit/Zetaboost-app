@echo off
chcp 65001 >nul
title ZetaBoost - Ejecutar (modo desarrollo)
color 0B

python --version >nul 2>&1
if errorlevel 1 (
    color 0C
    echo [ERROR] Python no esta instalado. Descargalo de https://www.python.org/downloads/
    echo Marca "Add Python to PATH" al instalar.
    start https://www.python.org/downloads/
    pause
    exit /b 1
)

if not exist ".venv" (
    echo Creando entorno virtual...
    python -m venv .venv
)

call .venv\Scripts\activate.bat
pip install -r requirements.txt >nul
echo Iniciando ZetaBoost...
python main.py
pause
