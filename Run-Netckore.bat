@echo off
REM Netckore Portable Launcher
REM Double-click this file to start Netckore without installation.
REM The app clears its own Mark of the Web automatically.

REM Unblock the executable (quietly)
powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -Command "Unblock-File -LiteralPath '%CD%\Netckore.exe' -ErrorAction SilentlyContinue" >nul 2>&1

start "" "%CD%\Netckore.exe"
