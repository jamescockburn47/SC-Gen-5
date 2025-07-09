#!/bin/bash
# ================================================
# SC Gen 5 - Cleanup Old Startup Scripts
# ================================================
# This removes old startup scripts to avoid confusion
# Keep only: start_sc_gen5.sh

echo "================================================"
echo "   SC Gen 5 - Cleaning Up Old Scripts"
echo "================================================"
echo

# List of scripts to remove (old startup scripts)
OLD_SCRIPTS=(
    "START_HERE.sh"
    "start_full_stack.sh"
    "start_frontend_wsl.sh"
    "restart_with_memory_fix.sh"
    "run_services.py"
    "launch_sc_gen5.py"
    "quick_launcher.py"
    "simple_launch.py"
    "smart_launcher.py"
    "desktop_launcher.py"
    "env_aware_launcher.py"
    "wsl_launcher.py"
    "wsl_full_launcher.py"
    "launch_frontend.py"
    "start_sophisticated_ui.py"
    "create_shortcut.py"
    "create_scgen5_shortcut.py"
)

echo "Removing old startup scripts..."
echo

for script in "${OLD_SCRIPTS[@]}"; do
    if [ -f "$script" ]; then
        echo "Removing: $script"
        rm "$script"
    fi
done

echo
echo "================================================"
echo "   ✅ Cleanup Complete!"
echo "================================================"
echo
echo "🎯 Now you have ONLY these launchers:"
echo "   ✅ start_sc_gen5.sh - Main Linux/WSL script"
echo "   ✅ SC_Gen5_Launcher.bat - Windows launcher"
echo "   ✅ Stop_SC_Gen5.bat - Windows stop script"
echo "   ✅ setup_windows_shortcut.bat - Windows setup"
echo
echo "💡 To use:"
echo "   Linux/WSL: ./start_sc_gen5.sh start"
echo "   Windows: Double-click SC_Gen5_Launcher.bat"
echo
echo "🚫 No more multiple startup scripts to confuse you!" 