# Windows Desktop Setup for SC Gen 5

## Quick Start (Recommended)

### Option 1: Desktop Shortcut (Easiest)

1. **Copy the project to your desktop:**
   ```
   Copy your "SC Gen 5" folder to your Windows Desktop
   ```

2. **Double-click to start:**
   ```
   Double-click START_SC_GEN_5.bat on your desktop
   ```

3. **That's it!** The system will:
   - Start the backend server
   - Start the frontend
   - Open your browser automatically
   - Show you the URLs

### Option 2: Manual Startup

1. **Open Command Prompt** in your SC Gen 5 folder
2. **Run the startup script:**
   ```cmd
   start_sc_gen_5_windows_simple.bat
   ```

## What Each File Does

- `START_SC_GEN_5.bat` - Desktop shortcut (double-click to start)
- `start_sc_gen_5_windows_simple.bat` - Main startup script
- `start_sc_gen_5_windows.bat` - Advanced startup with more features

## URLs After Startup

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8001/docs
- **Health Check**: http://localhost:8001/api/rag/status

## Troubleshooting

### If it doesn't start:
1. Make sure Python and Node.js are installed
2. Check that the SC Gen 5 folder is on your desktop
3. Try running as Administrator

### If ports are in use:
- The script will automatically kill existing processes
- If it fails, manually close any Python or Node.js processes

### To stop the system:
- Close the command prompt windows
- Or press Ctrl+C in each window

## File Locations

```
Desktop/
└── SC Gen 5/
    ├── START_SC_GEN_5.bat          ← Desktop shortcut
    ├── start_sc_gen_5_windows_simple.bat
    ├── app.py
    ├── frontend/
    └── ... (other files)
```

## Quick Commands

```cmd
# Start the system
START_SC_GEN_5.bat

# Or from command line
cd "Desktop\SC Gen 5"
start_sc_gen_5_windows_simple.bat
``` 