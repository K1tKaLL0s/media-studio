@echo off
powershell.exe -NoProfile -File "%~dp0scripts\start-gateway.ps1" -Studio
if errorlevel 1 pause
