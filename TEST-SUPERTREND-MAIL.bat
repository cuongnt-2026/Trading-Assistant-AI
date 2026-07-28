@echo off
chcp 65001 >nul
title Test mail SUPERTREND
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (set "PY=.venv\Scripts\python.exe") else (set "PY=python")
echo Dang gui MAIL MAU Supertrend toi hop thu cua ban...
"%PY%" send_test_supertrend.py
echo.
pause
