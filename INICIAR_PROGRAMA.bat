@echo off
cd /d "%~dp0"
where pyw >nul 2>nul
if %errorlevel%==0 (
    start "" pyw subneteo_vlsm.py
    exit /b
)
where pythonw >nul 2>nul
if %errorlevel%==0 (
    start "" pythonw subneteo_vlsm.py
    exit /b
)
echo No se encontro Python instalado.
echo Instalalo desde https://www.python.org/downloads/
pause
