@echo off
REM Netckore launcher - Windows (source checkout)
REM
REM Double-click this file to launch Netckore from the project folder.
REM The app clears the Mark of the Web from its own files at startup.

if exist "dist\Netckore\Netckore.exe" (
    powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -Command "Unblock-File -LiteralPath '%CD%\dist\Netckore\Netckore.exe' -ErrorAction SilentlyContinue" >nul 2>&1
    start "" "%CD%\dist\Netckore\Netckore.exe"
) else (
    python -m netckore
)