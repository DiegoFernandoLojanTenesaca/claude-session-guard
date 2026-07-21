@echo off
REM Instalador fácil para Windows: doble clic aquí.
cd /d "%~dp0"
py install.py 2>nul || python install.py
echo.
pause
