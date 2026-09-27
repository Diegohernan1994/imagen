@echo off
title Instalador Todo-En-Uno - California Remodeling Photo Enhancer
color 0B
cd /d "%~dp0"

echo =======================================================================
echo   SISTEMA DE MEJORA DE FOTOS - CALIFORNIA REMODELING
echo   Instalador y Configurador Automatico
echo =======================================================================
echo.

set PY_CMD=none

:: 1. Verificar si Python ya existe en el sistema
echo [1/3] Verificando componentes en tu equipo...
where python >nul 2>&1
if %errorlevel% equ 0 (
    set PY_CMD=python
    goto :PYTHON_READY
)

where py >nul 2>&1
if %errorlevel% equ 0 (
    set PY_CMD=py
    goto :PYTHON_READY
)

for %%v in (313 312 311 310) do (
    if exist "%LOCALAPPDATA%\Programs\Python\Python%%v\python.exe" (
        set PY_CMD="%LOCALAPPDATA%\Programs\Python\Python%%v\python.exe"
        goto :PYTHON_READY
    )
)

:: 2. Si no tiene Python, descargar con barra de progreso visual
echo.
echo [AVISO] Python no esta presente en tu equipo.
echo [DESCARGANDO] Iniciando descarga de Python oficial (64 bits)...
echo.

powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Write-Host 'Conectando con servidores oficiales...'; (New-Object System.Net.WebClient).DownloadFile('https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe', '%TEMP%\python_installer.exe'); Write-Host 'Descarga completada con exito.'"

if not exist "%TEMP%\python_installer.exe" (
    color 0C
    echo.
    echo [ERROR] No se pudo descargar Python automaticamente.
    echo Revisa tu conexion a Internet o descargalo de https://www.python.org/downloads/
    pause
    exit /b 1
)

echo.
echo [INSTALANDO] Configurando Python en segundo plano...
start /wait "" "%TEMP%\python_installer.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_pip=1 SimpleInstall=1
del "%TEMP%\python_installer.exe" >nul 2>&1

set "PATH=%LOCALAPPDATA%\Programs\Python\Python311;%LOCALAPPDATA%\Programs\Python\Python311\Scripts;%PATH%"

where python >nul 2>&1
if %errorlevel% equ 0 (
    set PY_CMD=python
    goto :PYTHON_READY
)
if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
    set PY_CMD="%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    goto :PYTHON_READY
)

color 0C
echo.
echo Instalacion de Python completada. Por favor abre "INICIAR_SISTEMA.bat".
pause
exit /b 0

:PYTHON_READY
echo [OK] Motor Python detectado y listo:
%PY_CMD% --version
echo.

:: 3. Descarga e instalacion de librerias con progreso
echo [2/3] Descargando e instalando librerias graficas (OpenCV, Pillow, Streamlit)...
echo      Veras el avance de descarga en pantalla:
echo.

%PY_CMD% -m pip install --upgrade pip
%PY_CMD% -m pip install opencv-python pillow numpy tqdm streamlit

echo.
echo =======================================================================
echo   [3/3] INSTALACION 100%% COMPLETADA CON EXITO!
echo.
echo   Todo esta listo y configurado.
echo   REDIRECCIONANDO AL SISTEMA EN 3 SEGUNDOS...
echo   (Se abrira automaticamente en tu navegador web)
echo =======================================================================
echo.

timeout /t 3 >nul

:: Redireccion automatica y lanzamiento del sistema
%PY_CMD% -m streamlit run app.py
