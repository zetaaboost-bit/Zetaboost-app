@echo off
chcp 65001 >nul
title ZetaBoost - Constructor de EXE
color 0B

echo ==========================================================
echo   ZetaBoost - CONSTRUCTOR AUTOMATICO DE .EXE
echo ==========================================================
echo.

REM ---- 1. Verificar Python ----
python --version >nul 2>&1
if errorlevel 1 (
    color 0C
    echo [ERROR] Python no esta instalado o no esta en el PATH.
    echo.
    echo  1. Descarga Python 3.11 desde:
    echo     https://www.python.org/downloads/
    echo.
    echo  2. MUY IMPORTANTE durante la instalacion:
    echo     Marca la casilla  "Add Python to PATH"
    echo.
    echo  3. Cuando termine, vuelve a hacer doble clic en este archivo.
    echo.
    start https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [OK] Python detectado:
python --version
echo.

REM ---- 2. Crear entorno virtual ----
if not exist ".venv" (
    echo [1/4] Creando entorno virtual...
    python -m venv .venv
) else (
    echo [1/4] Entorno virtual ya existe, reutilizando...
)

call .venv\Scripts\activate.bat

REM ---- 3. Instalar dependencias ----
echo [2/4] Instalando dependencias (puede tardar unos minutos)...
python -m pip install --upgrade pip >nul
pip install -r requirements.txt
pip install pyinstaller
if errorlevel 1 (
    color 0C
    echo [ERROR] Fallo instalando dependencias. Revisa tu conexion a internet.
    pause
    exit /b 1
)

REM ---- 4. Compilar EXE ----
echo [3/4] Compilando ZetaBoost.exe (esto tarda 2-5 minutos)...
pyinstaller --noconfirm --clean --windowed --onefile --name ZetaBoost ^
    --collect-submodules PySide6 ^
    --hidden-import wmi ^
    --hidden-import win32com ^
    --hidden-import win32com.client ^
    --hidden-import pythoncom ^
    --add-data "assets;assets" ^
    main.py

if errorlevel 1 (
    color 0C
    echo [ERROR] La compilacion fallo. Copia el texto de arriba y pasalo al agente.
    pause
    exit /b 1
)

echo [4/4] Listo!
color 0A
echo.
echo ==========================================================
echo   EXITO! Tu ejecutable esta en:
echo   %cd%\dist\ZetaBoost.exe
echo ==========================================================
echo.
echo  IMPORTANTE: Ejecutalo con clic derecho ^> "Ejecutar como administrador"
echo  para que funcionen todas las optimizaciones.
echo.
start "" explorer "%cd%\dist"
pause
