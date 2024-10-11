@echo off
setlocal enabledelayedexpansion

set SKIP_INSTALL=0

:parse_args
if "%~1"=="-s" set SKIP_INSTALL=1
if "%~1"=="--skip-install" set SKIP_INSTALL=1
shift
if not "%~1"=="" goto parse_args

if %SKIP_INSTALL%==0 (
    echo Installing required packages...
    pip install -r requirements.txt
    if !errorlevel! neq 0 (
        echo Error: Failed to install required packages.
        pause
        exit /b 1
    )
    echo.
) else (
    echo Skipping package installation.
    echo.
)

echo Running PCA application
python pca_entry.py
if !errorlevel! neq 0 (
    echo Error: Failed to run PCA application.
    pause
    exit /b 1
)

pause