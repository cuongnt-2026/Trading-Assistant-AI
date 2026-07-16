@echo off
chcp 65001 >nul
title Trading Assistant AI - Giu may thuc (khong ngu, khong cat mang)

:: Tu nang quyen Admin
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Dang xin quyen Admin...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

echo ============================================================
echo   Dang cau hinh: KHONG ngu / KHONG hibernate / KHONG cat USB
echo ============================================================

:: Khi cam sac (AC): khong bao gio ngu / hibernate / tat man hinh
powercfg /change standby-timeout-ac 0
powercfg /change hibernate-timeout-ac 0
powercfg /change monitor-timeout-ac 0

:: Tat USB selective suspend (tranh cat WiFi USB / thiet bi)
powercfg /setacvalueindex SCHEME_CURRENT 2a737441-1930-4402-8d77-b2bebba308a3 48e6b7a6-50f5-4782-a5d4-53bb8f07e226 0
powercfg /setactive SCHEME_CURRENT

echo.
echo [OK] Da xong. May se KHONG tu ngu khi cam sac.
echo LUU Y: Van phai lam thu cong 2 viec trong Device Manager va MT5
echo        (chan tat card mang + MT5 tu dang nhap) de het bao "reset".
echo.
pause
