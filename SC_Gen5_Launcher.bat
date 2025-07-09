@echo off
REM ================================================
REM SC Gen 5 - Single Windows Desktop Launcher
REM ================================================
REM This is the ONLY launcher you need to use

echo.
echo ================================================
echo    SC Gen 5 - LexCognito AI Platform
echo ================================================
echo.

REM Check if WSL is running
wsl --status >nul 2>&1
if errorlevel 1 (
    echo Starting WSL...
    wsl --shutdown
    timeout /t 3 /nobreak >nul
    wsl
)

REM Start SC Gen 5 using the main script
echo Starting SC Gen 5...
wsl -d Ubuntu-22.04 -e bash -c "cd '/home/jcockburn/SC Gen 5' && ./start_sc_gen5.sh start"

REM Wait for services to start
echo Waiting for services to start...
timeout /t 10 /nobreak >nul

REM Open the frontend in default browser
echo Opening SC Gen 5 in browser...
start http://localhost:3000

echo.
echo ================================================
echo    SC Gen 5 is now running!
echo ================================================
echo Frontend: http://localhost:3000
echo Backend:  http://localhost:8001
echo.
echo To stop: Right-click this shortcut and select "Stop SC Gen 5"
echo.
pause