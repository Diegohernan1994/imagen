@echo off
title Lanzador - California Remodeling Photo Enhancer
color 0B
cd /d "%~dp0"

set PY_CMD=none

where python >nul 2>&1
if %errorlevel% equ 0 (
    set PY_CMD=python
    goto :START_APP
)

where py >nul 2>&1
if %errorlevel% equ 0 (
    set PY_CMD=py
    goto :START_APP
)

if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    set PY_CMD="%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    goto :START_APP
)
if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
    set PY_CMD="%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    goto :START_APP
)
if exist "%LOCALAPPDATA%\Programs\Python\Python310\python.exe" (
    set PY_CMD="%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
    goto :START_APP
)

color 0C
echo [ERROR] No se detecto Python en el sistema.
echo Por favor ejecuta primero "INSTALAR_DEPENDENCIAS.bat".
pause
exit /b 1

:START_APP
echo =======================================================
echo   Iniciando California Remodeling Photo Enhancer...
echo =======================================================
%PY_CMD% -m streamlit run app.py
if %errorlevel% neq 0 (
    echo.
    echo Ocurrio un problema al iniciar. Asegurate de haber corrido
    echo primero INSTALAR_DEPENDENCIAS.bat
    echo.
    pause
)
