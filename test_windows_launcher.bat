@echo off
REM ================================================
REM SC Gen 5 - Windows Launcher Test
REM ================================================

echo.
echo ================================================
echo    Testing Windows Launcher...
echo ================================================
echo.

echo Testing WSL connection...
wsl -d Ubuntu-22.04 -e bash -c "echo 'WSL connection successful'"

echo.
echo Testing project directory access...
wsl -d Ubuntu-22.04 -e bash -c "cd '/home/jcockburn/SC Gen 5' && pwd && ls -la start_sc_gen5.sh"

echo.
echo Testing main script execution...
wsl -d Ubuntu-22.04 -e bash -c "cd '/home/jcockburn/SC Gen 5' && ./start_sc_gen5.sh status"

echo.
echo ================================================
echo    ✅ Windows launcher test completed!
echo ================================================
echo.
echo If you see the status above, the launcher will work.
echo.
pause 