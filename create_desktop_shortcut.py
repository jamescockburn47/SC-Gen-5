#!/usr/bin/env python3
"""
Create Windows Desktop Shortcut for SC Gen 5
This creates a single desktop shortcut that uses the main start_sc_gen5.sh script
"""

import os
import sys
import subprocess
from pathlib import Path
import winreg

def get_desktop_path():
    """Get the Windows desktop path."""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                           r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders") as key:
            desktop = winreg.QueryValueEx(key, "Desktop")[0]
            return Path(desktop)
    except:
        # Fallback to user's desktop
        return Path.home() / "Desktop"

def create_shortcut():
    """Create the desktop shortcut."""
    try:
        # Get current script directory
        script_dir = Path(__file__).parent.absolute()
        
        # Paths
        launcher_bat = script_dir / "SC_Gen5_Launcher.bat"
        stop_bat = script_dir / "Stop_SC_Gen5.bat"
        desktop_path = get_desktop_path()
        
        # Create VBS script for shortcut creation
        vbs_content = f'''
Set WshShell = WScript.CreateObject("WScript.Shell")
Set shortcut = WshShell.CreateShortcut("{desktop_path}\\SC Gen 5.lnk")
shortcut.TargetPath = "{launcher_bat}"
shortcut.WorkingDirectory = "{script_dir}"
shortcut.Description = "Launch SC Gen 5 - LexCognito AI Platform"
shortcut.IconLocation = "{script_dir}\\app.py,0"
shortcut.Save

Set shortcut2 = WshShell.CreateShortcut("{desktop_path}\\Stop SC Gen 5.lnk")
shortcut2.TargetPath = "{stop_bat}"
shortcut2.WorkingDirectory = "{script_dir}"
shortcut2.Description = "Stop SC Gen 5 - LexCognito AI Platform"
shortcut2.IconLocation = "{script_dir}\\app.py,0"
shortcut2.Save
'''
        
        # Write VBS script
        vbs_file = script_dir / "create_shortcut.vbs"
        with open(vbs_file, 'w') as f:
            f.write(vbs_content)
        
        # Execute VBS script
        subprocess.run(['cscript', '//nologo', str(vbs_file)], check=True)
        
        # Clean up
        vbs_file.unlink()
        
        print("✅ Desktop shortcuts created successfully!")
        print(f"📁 Location: {desktop_path}")
        print("🚀 Shortcut: 'SC Gen 5' - Launch the application")
        print("🛑 Shortcut: 'Stop SC Gen 5' - Stop the application")
        print()
        print("💡 Usage:")
        print("   - Double-click 'SC Gen 5' to start")
        print("   - Double-click 'Stop SC Gen 5' to stop")
        print("   - This uses the main start_sc_gen5.sh script")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating shortcut: {e}")
        return False

def main():
    """Main function."""
    print("================================================")
    print("   SC Gen 5 - Desktop Shortcut Creator")
    print("================================================")
    print()
    print("This will create a single Windows desktop shortcut")
    print("that uses the main start_sc_gen5.sh script.")
    print()
    
    if create_shortcut():
        print()
        print("🎉 Setup complete! You now have a single launcher.")
        print("   No more multiple startup scripts to manage!")
    else:
        print()
        print("❌ Setup failed. Please run manually:")
        print("   ./start_sc_gen5.sh start")

if __name__ == "__main__":
    main() 