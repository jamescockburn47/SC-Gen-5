@echo off
title Strategic Counsel Gen 5 Launcher
echo ================================================================
echo           STRATEGIC COUNSEL GEN 5 - WSL LAUNCHER
echo ================================================================
echo.
echo Starting services in WSL Ubuntu...
echo.

REM Run the Python launcher in WSL
wsl -d Ubuntu-22.04 -e python3 "/home/jcockburn/SC Gen 5/launch_sc_gen5.py"

echo.
echo Services stopped. Press any key to close...
pause >nul