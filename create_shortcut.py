#!/usr/bin/env python3
"""
Simple script to create SC Gen 5 desktop shortcut
"""

import sys
import os
from pathlib import Path

def create_desktop_shortcut():
    """Create desktop shortcut for SC Gen 5"""
    try:
        if sys.platform.startswith('win'):
            # Windows shortcut creation
            import winshell
            from win32com.client import Dispatch
            
            print("✅ Windows dependencies imported successfully")
            
            # Get desktop path
            desktop = winshell.desktop()
            print(f"Desktop path: {desktop}")
            
            # Get the launcher script path
            launcher_path = Path(__file__).parent / "test_server.py"
            print(f"Launcher path: {launcher_path}")
            
            # Create shortcut
            shortcut_path = Path(desktop) / "Strategic Counsel Gen 5.lnk"
            print(f"Creating shortcut at: {shortcut_path}")
            
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(str(shortcut_path))
            shortcut.Targetpath = sys.executable
            shortcut.Arguments = str(launcher_path)
            shortcut.WorkingDirectory = str(Path(__file__).parent)
            shortcut.IconLocation = str(launcher_path)
            shortcut.Description = "Strategic Counsel Gen 5 - Advanced Legal Research Assistant"
            shortcut.save()
            
            print("✅ Desktop shortcut created successfully!")
            print(f"📁 Location: {shortcut_path}")
            print("\n🎉 You can now double-click the shortcut on your desktop to launch SC Gen 5!")
            
            return True
                
        else:
            print("❌ This script is designed for Windows")
            return False
            
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please install: pip install pywin32 winshell")
        return False
        
    except Exception as e:
        print(f"❌ Error creating shortcut: {e}")
        return False

def main():
    """Main function"""
    print("SC Gen 5 - Desktop Shortcut Creator")
    print("=" * 40)
    
    success = create_desktop_shortcut()
    
    if success:
        print("\n" + "=" * 40)
        print("✅ Setup completed successfully!")
        print("\nNext steps:")
        print("1. Look for 'Strategic Counsel Gen 5' on your desktop")
        print("2. Double-click the shortcut to launch the application")
        print("3. The launcher will start all services automatically")
    else:
        print("\n❌ Setup failed. Please check the error messages above.")

if __name__ == "__main__":
    main() 