@echo off
title Launch Brave for HackFill Automation
echo ======================================================================
echo Launching Brave with HackFill Automation Port (Port 9222)
echo ======================================================================
echo This enables HackFill to attach to your open browser window directly.
echo All your tabs, bookmarks, and active login sessions will be preserved.
echo Zero new browser windows will be created during automation.
echo.

set BRAVE_PATH=C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe
if not exist "%BRAVE_PATH%" (
    set BRAVE_PATH=C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe
)
if not exist "%BRAVE_PATH%" (
    set BRAVE_PATH=%LOCALAPPDATA%\BraveSoftware\Brave-Browser\Application\brave.exe
)

echo Starting Brave from: "%BRAVE_PATH%"
start "" "%BRAVE_PATH%" --remote-debugging-port=9222 --restore-last-session
echo.
echo [SUCCESS] Brave is now running with automation port enabled!
echo You can now run HackFill and it will control this open browser window.
pause
