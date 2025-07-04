@echo off
echo 🎨 Starting React Frontend in WSL...
echo.

REM Run the frontend startup script in WSL
wsl -d Ubuntu-22.04 --cd "/home/jcockburn/SC Gen 5/frontend" bash start_frontend_wsl.sh

pause 