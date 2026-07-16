@echo off
chcp 65001 >nul
title Trading Assistant AI - Chan doan symbol
cd /d "%~dp0"
set "PY=python"
if exist ".venv\Scripts\python.exe" set "PY=.venv\Scripts\python.exe"
echo Hay mo MT5 va dang nhap truoc.
echo.
"%PY%" diag_symbols.py
echo.
pause
