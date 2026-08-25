@echo off
chcp 65001 >nul
title Xem thu Entry/SL/TP Bollinger + London (that, khong fake)
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (set "PY=.venv\Scripts\python.exe") else (set "PY=python")

echo ============================================================
echo   Quet nguoc lich su gan day de tim VI DU THAT gan nhat cho
echo   moi to hop Bollinger + London (khong ep tin hieu gia nhu ban truoc)
echo   Co the mat vai chuc giay vi phai quet nhieu nen.
echo ============================================================
echo LUU Y: mo MT5 va dang nhap truoc.
echo.
"%PY%" demo_live_signals.py
echo.
pause
