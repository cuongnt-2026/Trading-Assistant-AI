@echo off
REM ============================================================
REM  Trading Assistant AI - chay bot canh tin hieu (tu restart)
REM  Neu bot bi loi/crash se tu bat lai sau 15 giay.
REM  Dong cua so nay HOAC dung Task Scheduler de dung han.
REM ============================================================

REM Chuyen ve thu muc chua file .bat nay
cd /d "%~dp0"

REM Dung python trong .venv neu co, khong thi dung python he thong
if exist ".venv\Scripts\python.exe" (
    set "PY=.venv\Scripts\python.exe"
) else (
    set "PY=python"
)

if not exist "logs" mkdir "logs"

:loop
echo [%date% %time%] Starting Trading Assistant AI bot... >> "logs\bot.log"
"%PY%" run_monitor.py >> "logs\bot.log" 2>&1
echo [%date% %time%] Bot stopped (exit %errorlevel%). Restart sau 15s... >> "logs\bot.log"
timeout /t 15 /nobreak >nul
goto loop
