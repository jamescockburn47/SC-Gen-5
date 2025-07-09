@echo off
REM ================================================
REM SC Gen 5 - Windows Shortcut Setup
REM ================================================

echo.
echo ================================================
echo    SC Gen 5 - Desktop Shortcut Setup
echo ================================================
echo.

REM Get the project directory (Windows path)
set "PROJECT_DIR=%~dp0"
set "DESKTOP_DIR=%USERPROFILE%\Desktop"

echo Creating desktop shortcuts...
echo Project Directory: %PROJECT_DIR%
echo Desktop Directory: %DESKTOP_DIR%

REM Create VBS script for shortcut creation
echo Set WshShell = WScript.CreateObject("WScript.Shell") > "%TEMP%\create_shortcuts.vbs"
echo Set shortcut = WshShell.CreateShortcut("%DESKTOP_DIR%\SC Gen 5.lnk") >> "%TEMP%\create_shortcuts.vbs"
echo shortcut.TargetPath = "%PROJECT_DIR%SC_Gen5_Launcher.bat" >> "%TEMP%\create_shortcuts.vbs"
echo shortcut.WorkingDirectory = "%PROJECT_DIR%" >> "%TEMP%\create_shortcuts.vbs"
echo shortcut.Description = "Launch SC Gen 5 - LexCognito AI Platform" >> "%TEMP%\create_shortcuts.vbs"
echo shortcut.IconLocation = "%PROJECT_DIR%app.py,0" >> "%TEMP%\create_shortcuts.vbs"
echo shortcut.Save >> "%TEMP%\create_shortcuts.vbs"

echo Set shortcut2 = WshShell.CreateShortcut("%DESKTOP_DIR%\Stop SC Gen 5.lnk") >> "%TEMP%\create_shortcuts.vbs"
echo shortcut2.TargetPath = "%PROJECT_DIR%Stop_SC_Gen5.bat" >> "%TEMP%\create_shortcuts.vbs"
echo shortcut2.WorkingDirectory = "%PROJECT_DIR%" >> "%TEMP%\create_shortcuts.vbs"
echo shortcut2.Description = "Stop SC Gen 5 - LexCognito AI Platform" >> "%TEMP%\create_shortcuts.vbs"
echo shortcut2.IconLocation = "%PROJECT_DIR%app.py,0" >> "%TEMP%\create_shortcuts.vbs"
echo shortcut2.Save >> "%TEMP%\create_shortcuts.vbs"

REM Execute VBS script
cscript //nologo "%TEMP%\create_shortcuts.vbs"

REM Clean up
del "%TEMP%\create_shortcuts.vbs"

echo.
echo ================================================
echo    ✅ Desktop shortcuts created successfully!
echo ================================================
echo.
echo 📁 Location: %DESKTOP_DIR%
echo 🚀 Shortcut: "SC Gen 5" - Launch the application
echo 🛑 Shortcut: "Stop SC Gen 5" - Stop the application
echo.
echo 💡 Usage:
echo    - Double-click "SC Gen 5" to start
echo    - Double-click "Stop SC Gen 5" to stop
echo    - This uses the main start_sc_gen5.sh script
echo.
echo 🎯 Remember: This is your SINGLE launcher system!
echo    No more multiple startup scripts to manage.
echo.
pause 