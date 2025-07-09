# SC Gen 5 - Single Launcher System

## 🎯 **ONE LAUNCHER TO RULE THEM ALL**

This system uses **ONE** main startup script: `start_sc_gen5.sh`

**DO NOT CREATE ADDITIONAL STARTUP SCRIPTS** - This causes confusion and maintenance issues.

## 📁 **Files You Need**

### Primary Launcher
- `start_sc_gen5.sh` - **THE MAIN SCRIPT** (Linux/WSL)
- `SC_Gen5_Launcher.bat` - Windows desktop shortcut
- `Stop_SC_Gen5.bat` - Windows stop shortcut

### Setup Script
- `create_desktop_shortcut.py` - Creates Windows shortcuts

## 🚀 **How to Use**

### Option 1: Windows Desktop Shortcut (Recommended)
1. Run: `python create_desktop_shortcut.py`
2. Double-click "SC Gen 5" on desktop to start
3. Double-click "Stop SC Gen 5" on desktop to stop

### Option 2: Direct WSL Commands
```bash
# Start
./start_sc_gen5.sh start

# Stop  
./start_sc_gen5.sh stop

# Restart
./start_sc_gen5.sh restart

# Status
./start_sc_gen5.sh status

# Clean restart
./start_sc_gen5.sh clean
```

## ⚠️ **IMPORTANT: No More Multiple Scripts**

### ❌ **DON'T CREATE THESE:**
- `start_full_stack.sh`
- `START_HERE.sh` 
- `run_services.py`
- `launch_sc_gen5.py`
- Any other startup scripts

### ✅ **ONLY USE THESE:**
- `start_sc_gen5.sh` - Main script
- `SC_Gen5_Launcher.bat` - Windows shortcut
- `Stop_SC_Gen5.bat` - Windows stop shortcut

## 🔧 **Why This Approach?**

1. **Single Source of Truth** - One script to maintain
2. **No Confusion** - Clear which script to use
3. **Consistent Behavior** - Same startup process every time
4. **Easy Debugging** - One place to fix issues
5. **Windows Integration** - Desktop shortcuts work seamlessly

## 📋 **Commands Available in start_sc_gen5.sh**

| Command | Description |
|---------|-------------|
| `start` | Start backend and frontend |
| `stop` | Stop all services |
| `restart` | Restart all services |
| `clean` | Clean shutdown and restart |
| `status` | Check if services are running |

## 🎯 **Remember**

- **ONE** main script: `start_sc_gen5.sh`
- **ONE** Windows launcher: `SC_Gen5_Launcher.bat`
- **ONE** stop script: `Stop_SC_Gen5.bat`

**When making changes, update the main script, not create new ones!**

## 🚫 **What NOT to Do**

- ❌ Don't create new startup scripts
- ❌ Don't modify multiple launchers
- ❌ Don't create separate scripts for different use cases
- ❌ Don't forget which script is the "main" one

## ✅ **What TO Do**

- ✅ Use `start_sc_gen5.sh` for all startup needs
- ✅ Update the main script when making changes
- ✅ Use Windows shortcuts for easy access
- ✅ Keep it simple - one launcher to rule them all 