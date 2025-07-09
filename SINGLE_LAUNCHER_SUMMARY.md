# 🎯 SC Gen 5 - Single Launcher System

## ✅ **CLEANUP COMPLETE - NO MORE MULTIPLE SCRIPTS!**

All old startup scripts have been removed. You now have a **SINGLE** launcher system.

## 📁 **Your Launcher Files**

### Main Script (Linux/WSL)
- `start_sc_gen5.sh` - **THE ONLY SCRIPT YOU NEED**

### Windows Shortcuts
- `SC_Gen5_Launcher.bat` - Start SC Gen 5
- `Stop_SC_Gen5.bat` - Stop SC Gen 5
- `setup_windows_shortcut.bat` - Create desktop shortcuts

## 🚀 **How to Use**

### From Windows Desktop
1. Run `setup_windows_shortcut.bat` (one time setup)
2. Double-click "SC Gen 5" on desktop to start
3. Double-click "Stop SC Gen 5" on desktop to stop

### From WSL/Linux
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

## 🚫 **REMEMBER: NO MORE MULTIPLE SCRIPTS**

### ❌ **DON'T CREATE THESE EVER AGAIN:**
- `start_full_stack.sh`
- `START_HERE.sh`
- `run_services.py`
- `launch_sc_gen5.py`
- Any other startup scripts

### ✅ **ONLY USE THESE:**
- `start_sc_gen5.sh` - Main script
- `SC_Gen5_Launcher.bat` - Windows launcher
- `Stop_SC_Gen5.bat` - Windows stop script

## 🎯 **Why This Approach?**

1. **Single Source of Truth** - One script to maintain
2. **No Confusion** - Clear which script to use
3. **Consistent Behavior** - Same startup process every time
4. **Easy Debugging** - One place to fix issues
5. **Windows Integration** - Desktop shortcuts work seamlessly

## 📋 **Available Commands**

| Command | Description |
|---------|-------------|
| `start` | Start backend and frontend |
| `stop` | Stop all services |
| `restart` | Restart all services |
| `clean` | Clean shutdown and restart |
| `status` | Check if services are running |

## 🔧 **When Making Changes**

**ALWAYS** update `start_sc_gen5.sh` - don't create new scripts!

```bash
# Edit the main script
nano start_sc_gen5.sh

# Test your changes
./start_sc_gen5.sh restart
```

## 🎉 **Benefits of Single Launcher**

- ✅ **No confusion** about which script to use
- ✅ **Easy maintenance** - one script to update
- ✅ **Consistent behavior** across all launches
- ✅ **Windows integration** with desktop shortcuts
- ✅ **Clear documentation** - one place to look

## 🚨 **IMPORTANT REMINDER**

**When you make changes to the system:**
1. Update `start_sc_gen5.sh` 
2. **DO NOT** create new startup scripts
3. **DO NOT** modify multiple launchers
4. Keep it simple - one launcher to rule them all!

---

**🎯 This is your SINGLE launcher system. Keep it that way!** 