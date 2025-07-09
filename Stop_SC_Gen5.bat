@echo off
REM ================================================
REM SC Gen 5 - Stop Script
REM ================================================

echo.
echo ================================================
echo    Stopping SC Gen 5...
echo ================================================
echo.

REM Stop SC Gen 5 using the main script
echo Stopping SC Gen 5 services...
wsl -d Ubuntu-22.04 -e bash -c "cd '/home/jcockburn/SC Gen 5' && ./start_sc_gen5.sh stop"

echo.
echo ================================================
echo    SC Gen 5 stopped successfully!
echo ================================================
echo.
pause 