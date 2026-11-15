@echo off
rem Doble clic para instalar (solo la primera vez) y abrir TerraPulso en Windows.
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Creando entorno de Python...
    py -m venv .venv 2>nul || python -m venv .venv
)
if not exist ".venv\Scripts\python.exe" (
    echo.
    echo No se encontro Python. Instalalo desde https://www.python.org/downloads/
    echo y marca la casilla "Add python.exe to PATH" durante la instalacion.
    pause
    exit /b 1
)
echo Instalando librerias (la primera vez tarda unos minutos)...
".venv\Scripts\python.exe" -m pip install -q -r requirements.txt
echo Abriendo TerraPulso en el navegador...
".venv\Scripts\python.exe" -m streamlit run app.py
pause
