@echo off
chcp 65001 >nul
title Trading Assistant AI - Signal Monitor
cd /d "%~dp0"

echo ============================================
echo    TRADING ASSISTANT AI - KHOI DONG BOT
echo ============================================
echo.

REM --- Chong may vao Sleep khi dang chay (khi cam dien) ---
powercfg /change standby-timeout-ac 0 >nul 2>&1
powercfg /change hibernate-timeout-ac 0 >nul 2>&1
echo [OK] Da tat Sleep (khi cam dien).

REM --- Chon Python: uu tien .venv, khong thi python he thong ---
set "PY=python"
if exist ".venv\Scripts\python.exe" set "PY=.venv\Scripts\python.exe"
echo [i] Python: %PY%

REM --- Kiem tra thu vien; neu thieu thi tu cai ---
"%PY%" -c "import MetaTrader5, pandas, ta" 1>nul 2>nul
if errorlevel 1 (
    echo [i] Thieu thu vien - dang tu cai tu requirements.txt ...
    "%PY%" -m pip install -r requirements.txt
)

REM --- Kiem tra lai ---
"%PY%" -c "import MetaTrader5, pandas, ta" 1>nul 2>nul
if errorlevel 1 (
    echo.
    echo [LOI] Van thieu thu vien sau khi cai. Xem thong bao pip ben tren.
    echo Co the Python nay khong co MetaTrader5. Hay cai: "%PY%" -m pip install MetaTrader5 pandas ta
    echo.
    pause
    exit /b
)

echo [OK] Du thu vien.
echo.
echo LUU Y: Hay mo MT5 va DANG NHAP truoc.
echo Bot dang chay... co tin hieu BUY/SELL se gui mail. (Ctrl+C de dung)
echo.

"%PY%" run_monitor.py

echo.
echo ============================================
echo    BOT DA DUNG. (Xem dong loi ben tren neu co)
echo ============================================
pause
