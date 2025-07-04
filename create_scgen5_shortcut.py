import os
import sys
from pathlib import Path
import winshell
from win32com.client import Dispatch

# Get user's desktop path
DESKTOP = winshell.desktop()

# WSL distribution name and project path
WSL_DISTRO = "Ubuntu-22.04"
PROJECT_PATH = "/home/jcockburn/SC Gen 5"

# Shortcut properties
shortcut_name = "Start SC Gen 5.lnk"
shortcut_path = os.path.join(DESKTOP, shortcut_name)

# Command to run in WSL
target = f"wsl.exe -d {WSL_DISTRO} -- cd '{PROJECT_PATH}' && python3 run_services.py"

# Optional: set icon (can be omitted or set to python.exe)
icon_path = sys.executable  # Use Python icon

# Create the shortcut
shell = Dispatch('WScript.Shell')
shortcut = shell.CreateShortCut(shortcut_path)
shortcut.Targetpath = "wsl.exe"
shortcut.Arguments = f"-d {WSL_DISTRO} -- cd '{PROJECT_PATH}' && python3 run_services.py"
shortcut.WorkingDirectory = DESKTOP
shortcut.IconLocation = icon_path
shortcut.save()

print(f"Shortcut created on desktop: {shortcut_path}") 