@echo off
REM SC Gen 5 Windows Launcher (for WSL)

echo Starting Strategic Counsel Gen 5...
echo.

REM Start WSL and run the launcher
wsl -d Ubuntu -e bash -c "cd '/home/jcockburn/SC Gen 5' && ./start_sc_gen5.sh"

pause