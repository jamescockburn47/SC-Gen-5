#!/usr/bin/env python3
"""
Test script for desktop shortcut creation
"""

import sys
import os
from pathlib import Path

def test_desktop_shortcut():
    """Test desktop shortcut creation"""
    print("Testing desktop shortcut creation...")
    
    try:
        if sys.platform.startswith('win'):
            # Test Windows shortcut creation
            import winshell
            from win32com.client import Dispatch
            
            print("✅ Windows dependencies imported successfully")
            
            # Get desktop path
            desktop = winshell.desktop()
            print(f"Desktop path: {desktop}")
            
            # Create shortcut
            shortcut_path = Path(desktop) / "SC Gen 5 Test.lnk"
            print(f"Creating shortcut at: {shortcut_path}")
            
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(str(shortcut_path))
            shortcut.Targetpath = sys.executable
            shortcut.Arguments = str(Path(__file__).absolute())
            shortcut.WorkingDirectory = str(Path(__file__).parent)
            shortcut.IconLocation = str(Path(__file__).absolute())
            shortcut.save()
            
            print("✅ Desktop shortcut created successfully!")
            
            # Clean up
            if shortcut_path.exists():
                shortcut_path.unlink()
                print("✅ Test shortcut cleaned up")
                
        else:
            print("❌ Not on Windows platform")
            
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please install: pip install pywin32 winshell")
        
    except Exception as e:
        print(f"❌ Error creating shortcut: {e}")

def test_auto_start():
    """Test auto-start setup"""
    print("\nTesting auto-start setup...")
    
    try:
        if sys.platform.startswith('win'):
            import winreg
            
            print("✅ Windows registry access available")
            
            # Test registry access
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
            winreg.CloseKey(key)
            
            print("✅ Registry access successful")
            
        else:
            print("❌ Not on Windows platform")
            
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        
    except Exception as e:
        print(f"❌ Error with auto-start: {e}")

if __name__ == "__main__":
    print("SC Gen 5 - Desktop Integration Test")
    print("=" * 40)
    
    test_desktop_shortcut()
    test_auto_start()
    
    print("\nTest completed!") 