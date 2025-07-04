@echo off
echo 🔧 Fixing Frontend Dependencies...
echo.

REM Run the fix in WSL
wsl -d Ubuntu-22.04 --cd "/home/jcockburn/SC Gen 5/frontend" bash -c "rm -rf node_modules package-lock.json && npm install"

echo.
echo ✅ Frontend dependencies fixed!
echo 🚀 Starting React development server...
echo.

REM Start the frontend
wsl -d Ubuntu-22.04 --cd "/home/jcockburn/SC Gen 5/frontend" npm start

pause 