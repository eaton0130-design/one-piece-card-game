@echo off
chcp 65001>nul
title 🏴‍☠️ 航海王卡牌冒險 - 啟動器 🏴‍☠️
cls

echo ==============================================
echo        🏴‍☠️ 歡迎來到航海王卡牌冒險！ 🏴‍☠️
echo ==============================================
echo.
echo [系統提示] 正在為你揚帆、檢查 Python 環境...

:: 檢查有沒有安裝 Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ❌ 偵測到這台電腦還沒安裝 Python！
    echo 🏴‍☠️ 魯夫正在發動「橡膠橡膠--自動安裝大法」...
    echo --------------------------------------------------
    
    :: 執行 Windows 內建的自動安裝指令
    winget install Python.Python.3 --silent --accept-source-agreements --accept-package-agreements
    
    echo --------------------------------------------------
    echo 🎉 哇！魯夫已經幫你把 Python 裝好囉！
    echo ⚠️  提示：因為是第一次安裝，請關閉這個視窗，重新點擊一次啟動器就能開玩囉！
    pause
    exit
)

echo [系統提示] 環境檢查成功！正在加載船員與存檔...
echo.
timeout /t 2 >nul

:: 啟動你的遊戲
python main.py

echo.
echo ==============================================
echo        ⚓ 感謝你的冒險，海賊團已安全返航！ ⚓
echo ==============================================
pause