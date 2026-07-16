<#
============================================================
 Trading Assistant AI - Setup chay ngam 24/7
------------------------------------------------------------
 Script nay se:
   1. Tat che do NGU (sleep/hibernate) khi cam dien -> may khong tu ngat.
   2. Tao Scheduled Task tu mo BOT khi ban dang nhap Windows.
   3. (Tuy chon) Tu mo MetaTrader 5 khi dang nhap, neu ban chi ra duong dan.

 CACH CHAY (chuot phai -> Run with PowerShell, hoac):
   powershell -ExecutionPolicy Bypass -File scripts\setup_always_on.ps1
   powershell -ExecutionPolicy Bypass -File scripts\setup_always_on.ps1 -Mt5Path "C:\Program Files\MetaTrader 5\terminal64.exe"

 GO BO cai dat:
   powershell -ExecutionPolicy Bypass -File scripts\setup_always_on.ps1 -Uninstall
============================================================
#>

param(
    [string]$Mt5Path = "",
    [switch]$Uninstall
)

$ErrorActionPreference = "Stop"

# Thu muc goc du an = thu muc cha cua scripts\
$ProjectDir = Split-Path -Parent $PSScriptRoot
$BotBat     = Join-Path $ProjectDir "run_bot.bat"

$TaskBot = "TradingAssistantAI_Bot"
$TaskMt5 = "TradingAssistantAI_MT5"

function Remove-TaskIfExists($name) {
    $t = Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
    if ($t) {
        Unregister-ScheduledTask -TaskName $name -Confirm:$false
        Write-Host "  - Da xoa task: $name"
    }
}

if ($Uninstall) {
    Write-Host "Dang go bo cau hinh 24/7..."
    Remove-TaskIfExists $TaskBot
    Remove-TaskIfExists $TaskMt5
    Write-Host "Xong. (Power settings khong bi doi lai, tu chinh trong Control Panel neu can.)"
    return
}

Write-Host "=============================================="
Write-Host " Trading Assistant AI - Setup chay ngam 24/7"
Write-Host "=============================================="
Write-Host "Project: $ProjectDir"

# ---------- 1) Tat che do ngu khi cam dien (AC) ----------
Write-Host "`n[1/3] Tat sleep/hibernate khi cam dien..."
powercfg /change standby-timeout-ac 0     | Out-Null   # khong tu ngu
powercfg /change hibernate-timeout-ac 0   | Out-Null   # khong tu ngu dong
powercfg /change disk-timeout-ac 0        | Out-Null   # khong tat o dia
# Man hinh co the tat sau 15 phut (khong anh huong bot, van tiet kiem dien)
powercfg /change monitor-timeout-ac 15    | Out-Null
Write-Host "  - Da tat auto-sleep. May se khong tu ngat khi cam dien."

# ---------- 2) Task tu chay BOT khi logon ----------
Write-Host "`n[2/3] Tao Scheduled Task tu chay BOT khi dang nhap..."
if (-not (Test-Path $BotBat)) {
    throw "Khong tim thay run_bot.bat tai: $BotBat"
}
Remove-TaskIfExists $TaskBot

$actionBot  = New-ScheduledTaskAction -Execute $BotBat -WorkingDirectory $ProjectDir
$triggerBot = New-ScheduledTaskTrigger -AtLogOn
# Settings: khong dung khi chay pin, khong gioi han thoi gian, tu chay lai neu loi
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit ([TimeSpan]::Zero) `
    -RestartCount 999 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -StartWhenAvailable

Register-ScheduledTask -TaskName $TaskBot `
    -Action $actionBot -Trigger $triggerBot -Settings $settings `
    -Description "Trading Assistant AI - bot canh tin hieu, tu chay khi dang nhap" `
    -RunLevel Highest | Out-Null
Write-Host "  - Da tao task: $TaskBot (chay khi ban dang nhap Windows)"

# ---------- 3) Task tu mo MT5 khi logon (tuy chon) ----------
Write-Host "`n[3/3] Cau hinh tu mo MetaTrader 5..."
if ($Mt5Path -ne "") {
    if (-not (Test-Path $Mt5Path)) {
        Write-Warning "  Khong thay MT5 tai: $Mt5Path -> bo qua. Ban co the mo MT5 thu cong."
    } else {
        Remove-TaskIfExists $TaskMt5
        $actionMt5  = New-ScheduledTaskAction -Execute $Mt5Path
        $triggerMt5 = New-ScheduledTaskTrigger -AtLogOn
        Register-ScheduledTask -TaskName $TaskMt5 `
            -Action $actionMt5 -Trigger $triggerMt5 -Settings $settings `
            -Description "Trading Assistant AI - tu mo MetaTrader 5 khi dang nhap" | Out-Null
        Write-Host "  - Da tao task: $TaskMt5 (tu mo MT5 khi dang nhap)"
    }
} else {
    Write-Host "  - Bo qua (khong nhap -Mt5Path). MT5 nen bat 'Start with Windows' hoac mo thu cong."
}

Write-Host "`n=============================================="
Write-Host " HOAN TAT!"
Write-Host "=============================================="
Write-Host "Tu gio khi may khoi dong & ban dang nhap:"
Write-Host "  - MT5 va bot tu chay (bot tu bat lai neu crash)."
Write-Host ""
Write-Host "QUAN TRONG khi di lam:"
Write-Host "  - KHOA man hinh bang Win+L  (bot VAN chay)."
Write-Host "  - KHONG 'Dang xuat/Sign out' (se tat bot)."
Write-Host "  - KHONG Shutdown (tru khi muon dung han)."
Write-Host ""
Write-Host "Chay thu ngay bay gio: mo run_bot.bat (nhay dup)."
Write-Host "Xem log: logs\bot.log"
