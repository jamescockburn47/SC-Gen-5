@echo off
echo ========================================
echo SC Gen 5 - Setup and Installation
echo ========================================
echo.

echo Installing Python dependencies...
python install_dependencies.py

echo.
echo Testing desktop shortcut creation...
python test_shortcut.py

echo.
echo Starting SC Gen 5 Desktop Launcher...
python desktop_launcher.py

pause 