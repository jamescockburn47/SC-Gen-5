#!/usr/bin/env python3
"""
Strategic Counsel Gen 5 - Enhanced Desktop Launcher
Advanced desktop integration with system tray, auto-start, and monitoring
"""

import os
import sys
import time
import json
import signal
import subprocess
import threading
import webbrowser
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import psutil

# Try to import desktop integration libraries
try:
    import pystray
    from pystray import MenuItem as Item
    from PIL import Image, ImageDraw
    SYSTEM_TRAY_AVAILABLE = True
except ImportError:
    SYSTEM_TRAY_AVAILABLE = False
    print("⚠️ System tray features require: pip install pystray pillow")

try:
    import tkinter as tk
    from tkinter import ttk, messagebox, filedialog
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False
    print("⚠️ GUI features require tkinter (usually included with Python)")


@dataclass
class ServiceConfig:
    """Configuration for a service"""
    name: str
    command: List[str]
    cwd: Optional[str] = None
    env: Optional[Dict[str, str]] = None
    port: Optional[int] = None
    health_url: Optional[str] = None
    auto_start: bool = True
    restart_on_failure: bool = True


@dataclass
class LauncherConfig:
    """Launcher configuration"""
    auto_start_on_boot: bool = False
    minimize_to_tray: bool = True
    check_health_interval: int = 30
    log_level: str = "INFO"
    browser_auto_open: bool = True
    theme: str = "dark"


class SystemMonitor:
    """System resource monitoring"""
    
    def __init__(self):
        self.start_time = time.time()
        
    def get_system_stats(self) -> Dict:
        """Get current system statistics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory usage
            memory = psutil.virtual_memory()
            
            # Disk usage
            disk = psutil.disk_usage('/')
            
            # GPU usage (if nvidia-ml-py is available)
            gpu_stats = self._get_gpu_stats()
            
            # Network stats
            network = psutil.net_io_counters()
            
            return {
                "cpu": {
                    "percent": cpu_percent,
                    "count": cpu_count
                },
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                    "used": memory.used
                },
                "disk": {
                    "total": disk.total,
                    "free": disk.free,
                    "percent": (disk.used / disk.total) * 100
                },
                "gpu": gpu_stats,
                "network": {
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv
                },
                "uptime": time.time() - self.start_time
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _get_gpu_stats(self) -> Dict:
        """Get GPU statistics if available"""
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0]  # Use first GPU
                return {
                    "name": gpu.name,
                    "load": gpu.load * 100,
                    "memory_used": gpu.memoryUsed,
                    "memory_total": gpu.memoryTotal,
                    "memory_percent": (gpu.memoryUsed / gpu.memoryTotal) * 100,
                    "temperature": gpu.temperature
                }
        except ImportError:
            # Try nvidia-ml-py
            try:
                import pynvml
                pynvml.nvmlInit()
                handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                
                name = pynvml.nvmlDeviceGetName(handle).decode('utf-8')
                mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
                
                return {
                    "name": name,
                    "load": util.gpu,
                    "memory_used": mem_info.used // 1024**2,  # MB
                    "memory_total": mem_info.total // 1024**2,  # MB
                    "memory_percent": (mem_info.used / mem_info.total) * 100,
                    "temperature": temp
                }
            except ImportError:
                pass
        except Exception:
            pass
        
        return {"available": False}


class EnhancedDesktopLauncher:
    """Enhanced desktop launcher with system tray and advanced features"""
    
    def __init__(self):
        self.root_dir = Path(__file__).parent
        self.config_file = self.root_dir / "launcher_config.json"
        self.log_file = self.root_dir / "launcher.log"
        
        # Load configuration
        self.config = self._load_config()
        
        # Initialize components
        self.processes: Dict[str, subprocess.Popen] = {}
        self.services = self._get_service_configs()
        self.monitor = SystemMonitor()
        self.tray_icon: Optional[pystray.Icon] = None
        self.gui_window: Optional[tk.Tk] = None
        self.running = True
        self.health_check_thread: Optional[threading.Thread] = None
        
        # Status tracking
        self.service_status: Dict[str, str] = {}
        self.last_health_check = {}
        
    def _load_config(self) -> LauncherConfig:
        """Load launcher configuration"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                return LauncherConfig(**data)
            except Exception as e:
                self._log(f"Failed to load config: {e}")
        
        # Return default config
        return LauncherConfig()
    
    def _save_config(self):
        """Save launcher configuration"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config.__dict__, f, indent=2)
        except Exception as e:
            self._log(f"Failed to save config: {e}")
    
    def _get_service_configs(self) -> List[ServiceConfig]:
        """Get service configurations"""
        return [
            ServiceConfig(
                name="Backend Services",
                command=[sys.executable, "run_services.py"],
                cwd=str(self.root_dir),
                port=8000,
                health_url="http://localhost:8000/health"
            ),
            ServiceConfig(
                name="Terminal Server",
                command=["npm", "start"],
                cwd=str(self.root_dir / "terminal-server"),
                port=3001,
                health_url="http://localhost:3001/health"
            ),
            ServiceConfig(
                name="React Frontend",
                command=["npm", "start"],
                cwd=str(self.root_dir / "frontend"),
                port=3000,
                health_url="http://localhost:3000"
            )
        ]
    
    def _log(self, message: str, level: str = "INFO"):
        """Log a message"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        
        print(log_entry)
        
        try:
            with open(self.log_file, 'a') as f:
                f.write(log_entry + "\n")
        except Exception:
            pass
    
    def create_tray_icon(self) -> Optional[pystray.Icon]:
        """Create system tray icon"""
        if not SYSTEM_TRAY_AVAILABLE:
            return None
        
        # Create icon image
        image = Image.new('RGB', (64, 64), color='blue')
        d = ImageDraw.Draw(image)
        d.text((10, 20), "SC5", fill='white')
        
        # Create menu
        menu = pystray.Menu(
            Item("Strategic Counsel Gen 5", self._show_gui, default=True),
            Item("Open Dashboard", lambda: webbrowser.open("http://localhost:3000")),
            Item("Open Terminal", lambda: webbrowser.open("http://localhost:3000/terminal")),
            pystray.Menu.SEPARATOR,
            Item("Start All Services", self._start_all_services),
            Item("Stop All Services", self._stop_all_services),
            Item("Restart Services", self._restart_all_services),
            pystray.Menu.SEPARATOR,
            Item("System Status", self._show_system_status),
            Item("Settings", self._show_settings),
            pystray.Menu.SEPARATOR,
            Item("Exit", self._quit_application)
        )
        
        return pystray.Icon("SC Gen 5", image, "Strategic Counsel Gen 5", menu)
    
    def start_service(self, service: ServiceConfig) -> bool:
        """Start a service"""
        try:
            self._log(f"Starting {service.name}...")
            
            env = os.environ.copy()
            if service.env:
                env.update(service.env)
            
            process = subprocess.Popen(
                service.command,
                cwd=service.cwd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            self.processes[service.name] = process
            self.service_status[service.name] = "starting"
            self._log(f"✅ {service.name} started (PID: {process.pid})")
            return True
            
        except Exception as e:
            self._log(f"❌ Failed to start {service.name}: {e}", "ERROR")
            self.service_status[service.name] = "failed"
            return False
    
    def stop_service(self, service_name: str) -> bool:
        """Stop a service"""
        if service_name not in self.processes:
            return True
        
        try:
            process = self.processes[service_name]
            self._log(f"Stopping {service_name}...")
            
            process.terminate()
            process.wait(timeout=10)
            
            del self.processes[service_name]
            self.service_status[service_name] = "stopped"
            self._log(f"✅ {service_name} stopped")
            return True
            
        except subprocess.TimeoutExpired:
            self._log(f"Force killing {service_name}...")
            process.kill()
            del self.processes[service_name]
            self.service_status[service_name] = "killed"
            return True
            
        except Exception as e:
            self._log(f"❌ Error stopping {service_name}: {e}", "ERROR")
            return False
    
    def check_service_health(self, service: ServiceConfig) -> bool:
        """Check if a service is healthy"""
        if not service.health_url:
            # If no health URL, just check if process is running
            return service.name in self.processes and self.processes[service.name].poll() is None
        
        try:
            import requests
            response = requests.get(service.health_url, timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def health_check_loop(self):
        """Background health checking loop"""
        while self.running:
            try:
                for service in self.services:
                    if service.name in self.processes:
                        is_healthy = self.check_service_health(service)
                        self.last_health_check[service.name] = {
                            "timestamp": time.time(),
                            "healthy": is_healthy
                        }
                        
                        if not is_healthy and service.restart_on_failure:
                            self._log(f"⚠️ {service.name} unhealthy, restarting...")
                            self.stop_service(service.name)
                            time.sleep(2)
                            self.start_service(service)
                
                time.sleep(self.config.check_health_interval)
                
            except Exception as e:
                self._log(f"Health check error: {e}", "ERROR")
                time.sleep(10)
    
    def create_desktop_shortcut(self):
        """Create desktop shortcut"""
        try:
            if sys.platform.startswith('win'):
                # Windows shortcut creation
                import winshell
                from win32com.client import Dispatch
                
                desktop = winshell.desktop()
                shortcut_path = Path(desktop) / "Strategic Counsel Gen 5.lnk"
                
                shell = Dispatch('WScript.Shell')
                shortcut = shell.CreateShortCut(str(shortcut_path))
                shortcut.Targetpath = sys.executable
                shortcut.Arguments = str(Path(__file__).absolute())
                shortcut.WorkingDirectory = str(self.root_dir)
                shortcut.IconLocation = str(Path(__file__).absolute())
                shortcut.save()
                
                self._log("✅ Desktop shortcut created")
                
            elif sys.platform.startswith('linux'):
                # Linux .desktop file
                desktop_file = f"""[Desktop Entry]
Name=Strategic Counsel Gen 5
Comment=Advanced Legal Research Assistant
Exec={sys.executable} {Path(__file__).absolute()}
Icon={self.root_dir}/icon.png
Terminal=false
Type=Application
Categories=Office;Development;
"""
                
                desktop_path = Path.home() / "Desktop" / "Strategic Counsel Gen 5.desktop"
                with open(desktop_path, 'w') as f:
                    f.write(desktop_file)
                
                # Make executable
                desktop_path.chmod(0o755)
                self._log("✅ Desktop shortcut created")
                
        except Exception as e:
            self._log(f"⚠️ Could not create desktop shortcut: {e}")
    
    def setup_auto_start(self, enable: bool = True):
        """Setup auto-start on system boot"""
        try:
            if sys.platform.startswith('win'):
                # Windows registry auto-start
                import winreg
                
                key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
                
                if enable:
                    command = f'"{sys.executable}" "{Path(__file__).absolute()}" --minimized'
                    winreg.SetValueEx(key, "Strategic Counsel Gen 5", 0, winreg.REG_SZ, command)
                    self._log("✅ Auto-start enabled")
                else:
                    try:
                        winreg.DeleteValue(key, "Strategic Counsel Gen 5")
                        self._log("✅ Auto-start disabled")
                    except FileNotFoundError:
                        pass
                
                winreg.CloseKey(key)
                
            elif sys.platform.startswith('linux'):
                # Linux autostart .desktop file
                autostart_dir = Path.home() / ".config" / "autostart"
                autostart_dir.mkdir(parents=True, exist_ok=True)
                
                autostart_file = autostart_dir / "strategic-counsel-gen5.desktop"
                
                if enable:
                    desktop_content = f"""[Desktop Entry]
Name=Strategic Counsel Gen 5
Comment=Advanced Legal Research Assistant
Exec={sys.executable} {Path(__file__).absolute()} --minimized
Icon={self.root_dir}/icon.png
Terminal=false
Type=Application
Hidden=false
X-GNOME-Autostart-enabled=true
"""
                    with open(autostart_file, 'w') as f:
                        f.write(desktop_content)
                    
                    autostart_file.chmod(0o755)
                    self._log("✅ Auto-start enabled")
                else:
                    if autostart_file.exists():
                        autostart_file.unlink()
                        self._log("✅ Auto-start disabled")
                        
        except Exception as e:
            self._log(f"⚠️ Could not setup auto-start: {e}")
    
    def _start_all_services(self, icon=None, item=None):
        """Start all services"""
        for service in self.services:
            if service.auto_start and service.name not in self.processes:
                self.start_service(service)
        
        # Open browser if configured
        if self.config.browser_auto_open:
            time.sleep(5)  # Wait for services to start
            webbrowser.open("http://localhost:3000")
    
    def _stop_all_services(self, icon=None, item=None):
        """Stop all services"""
        for service_name in list(self.processes.keys()):
            self.stop_service(service_name)
    
    def _restart_all_services(self, icon=None, item=None):
        """Restart all services"""
        self._stop_all_services()
        time.sleep(3)
        self._start_all_services()
    
    def _show_system_status(self, icon=None, item=None):
        """Show system status"""
        stats = self.monitor.get_system_stats()
        
        status_text = f"""Strategic Counsel Gen 5 System Status

Services:
"""
        for service in self.services:
            status = self.service_status.get(service.name, "stopped")
            health = self.last_health_check.get(service.name, {})
            health_status = "✅" if health.get("healthy", False) else "❌"
            status_text += f"  {service.name}: {status} {health_status}\n"
        
        status_text += f"""
System Resources:
  CPU: {stats.get('cpu', {}).get('percent', 0):.1f}%
  Memory: {stats.get('memory', {}).get('percent', 0):.1f}%
  Disk: {stats.get('disk', {}).get('percent', 0):.1f}%
"""
        
        if stats.get('gpu', {}).get('available', True):
            gpu = stats['gpu']
            status_text += f"  GPU: {gpu.get('load', 0):.1f}% ({gpu.get('memory_percent', 0):.1f}% VRAM)\n"
        
        if GUI_AVAILABLE:
            root = tk.Tk()
            root.title("System Status")
            root.geometry("400x300")
            
            text = tk.Text(root, wrap=tk.WORD, padx=10, pady=10)
            text.insert(tk.END, status_text)
            text.config(state=tk.DISABLED)
            text.pack(fill=tk.BOTH, expand=True)
            
            root.mainloop()
        else:
            print(status_text)
    
    def _show_settings(self, icon=None, item=None):
        """Show settings dialog"""
        if not GUI_AVAILABLE:
            self._log("GUI not available for settings")
            return
        
        # Create settings window
        settings_window = tk.Toplevel()
        settings_window.title("Strategic Counsel Gen 5 Settings")
        settings_window.geometry("500x400")
        
        # Auto-start setting
        auto_start_var = tk.BooleanVar(value=self.config.auto_start_on_boot)
        tk.Checkbutton(
            settings_window,
            text="Start automatically on system boot",
            variable=auto_start_var
        ).pack(pady=5)
        
        # Minimize to tray setting
        minimize_var = tk.BooleanVar(value=self.config.minimize_to_tray)
        tk.Checkbutton(
            settings_window,
            text="Minimize to system tray",
            variable=minimize_var
        ).pack(pady=5)
        
        # Browser auto-open setting
        browser_var = tk.BooleanVar(value=self.config.browser_auto_open)
        tk.Checkbutton(
            settings_window,
            text="Auto-open browser on startup",
            variable=browser_var
        ).pack(pady=5)
        
        # Health check interval
        tk.Label(settings_window, text="Health check interval (seconds):").pack(pady=5)
        interval_var = tk.IntVar(value=self.config.check_health_interval)
        tk.Spinbox(
            settings_window,
            from_=10,
            to=300,
            textvariable=interval_var
        ).pack(pady=5)
        
        def save_settings():
            self.config.auto_start_on_boot = auto_start_var.get()
            self.config.minimize_to_tray = minimize_var.get()
            self.config.browser_auto_open = browser_var.get()
            self.config.check_health_interval = interval_var.get()
            
            self._save_config()
            self.setup_auto_start(self.config.auto_start_on_boot)
            
            settings_window.destroy()
            messagebox.showinfo("Settings", "Settings saved successfully!")
        
        tk.Button(settings_window, text="Save", command=save_settings).pack(pady=20)
        tk.Button(settings_window, text="Cancel", command=settings_window.destroy).pack(pady=5)
    
    def _show_gui(self, icon=None, item=None):
        """Show main GUI window"""
        if not GUI_AVAILABLE:
            self._log("GUI not available")
            return
        
        if self.gui_window and self.gui_window.winfo_exists():
            self.gui_window.deiconify()
            self.gui_window.lift()
            return
        
        # Create main window
        self.gui_window = tk.Tk()
        self.gui_window.title("Strategic Counsel Gen 5 Launcher")
        self.gui_window.geometry("600x500")
        
        # Service controls
        services_frame = ttk.LabelFrame(self.gui_window, text="Services", padding=10)
        services_frame.pack(fill=tk.X, padx=10, pady=5)
        
        for i, service in enumerate(self.services):
            frame = ttk.Frame(services_frame)
            frame.pack(fill=tk.X, pady=2)
            
            ttk.Label(frame, text=service.name, width=20).pack(side=tk.LEFT)
            
            status_label = ttk.Label(frame, text="Stopped", width=10)
            status_label.pack(side=tk.LEFT, padx=5)
            
            ttk.Button(
                frame,
                text="Start",
                command=lambda s=service: self.start_service(s),
                width=8
            ).pack(side=tk.LEFT, padx=2)
            
            ttk.Button(
                frame,
                text="Stop",
                command=lambda s=service: self.stop_service(s.name),
                width=8
            ).pack(side=tk.LEFT, padx=2)
        
        # Control buttons
        control_frame = ttk.LabelFrame(self.gui_window, text="Control", padding=10)
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(control_frame, text="Start All", command=self._start_all_services).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Stop All", command=self._stop_all_services).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Restart All", command=self._restart_all_services).pack(side=tk.LEFT, padx=5)
        
        # Quick access
        access_frame = ttk.LabelFrame(self.gui_window, text="Quick Access", padding=10)
        access_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(
            access_frame,
            text="Open Dashboard",
            command=lambda: webbrowser.open("http://localhost:3000")
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            access_frame,
            text="Open Terminal",
            command=lambda: webbrowser.open("http://localhost:3000/terminal")
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            access_frame,
            text="API Docs",
            command=lambda: webbrowser.open("http://localhost:8000/docs")
        ).pack(side=tk.LEFT, padx=5)
        
        # System info
        info_frame = ttk.LabelFrame(self.gui_window, text="System Information", padding=10)
        info_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        info_text = tk.Text(info_frame, height=10)
        info_text.pack(fill=tk.BOTH, expand=True)
        
        def update_info():
            stats = self.monitor.get_system_stats()
            info_text.delete(1.0, tk.END)
            info_text.insert(tk.END, f"System Resources:\n")
            info_text.insert(tk.END, f"CPU: {stats.get('cpu', {}).get('percent', 0):.1f}%\n")
            info_text.insert(tk.END, f"Memory: {stats.get('memory', {}).get('percent', 0):.1f}%\n")
            info_text.insert(tk.END, f"Disk: {stats.get('disk', {}).get('percent', 0):.1f}%\n")
            
            if stats.get('gpu', {}).get('available', True):
                gpu = stats['gpu']
                info_text.insert(tk.END, f"GPU: {gpu.get('load', 0):.1f}% ({gpu.get('memory_percent', 0):.1f}% VRAM)\n")
            
            self.gui_window.after(5000, update_info)  # Update every 5 seconds
        
        update_info()
        
        # Handle window close
        def on_closing():
            if self.config.minimize_to_tray and SYSTEM_TRAY_AVAILABLE:
                self.gui_window.withdraw()
            else:
                self._quit_application()
        
        self.gui_window.protocol("WM_DELETE_WINDOW", on_closing)
        self.gui_window.mainloop()
    
    def _quit_application(self, icon=None, item=None):
        """Quit the application"""
        self.running = False
        
        # Stop all services
        self._stop_all_services()
        
        # Stop health check thread
        if self.health_check_thread:
            self.health_check_thread.join(timeout=2)
        
        # Stop tray icon
        if self.tray_icon:
            self.tray_icon.stop()
        
        # Close GUI
        if self.gui_window:
            self.gui_window.quit()
        
        sys.exit(0)
    
    def run(self):
        """Run the launcher"""
        self._log("🏛️ Strategic Counsel Gen 5 - Enhanced Desktop Launcher Starting...")
        
        # Check for command line arguments
        minimized = "--minimized" in sys.argv
        
        # Create desktop shortcut if it doesn't exist
        self.create_desktop_shortcut()
        
        # Setup auto-start if configured
        if self.config.auto_start_on_boot:
            self.setup_auto_start(True)
        
        # Start health check thread
        self.health_check_thread = threading.Thread(target=self.health_check_loop, daemon=True)
        self.health_check_thread.start()
        
        # Start system tray
        if SYSTEM_TRAY_AVAILABLE and self.config.minimize_to_tray:
            self.tray_icon = self.create_tray_icon()
            
            if minimized:
                # Run in background with tray only
                threading.Thread(target=self._start_all_services, daemon=True).start()
                self.tray_icon.run()
            else:
                # Start tray in background and show GUI
                threading.Thread(target=self.tray_icon.run, daemon=True).start()
                time.sleep(1)  # Give tray time to start
                
                # Auto-start services
                self._start_all_services()
                
                # Show GUI
                self._show_gui()
        else:
            # Fallback to console mode
            self._log("Running in console mode (system tray not available)")
            
            # Start services
            self._start_all_services()
            
            # Show console menu
            self._console_menu()
    
    def _console_menu(self):
        """Console-based menu for systems without GUI support"""
        while self.running:
            print("\n" + "="*50)
            print("Strategic Counsel Gen 5 - Desktop Launcher")
            print("="*50)
            print("1. Start all services")
            print("2. Stop all services") 
            print("3. Restart all services")
            print("4. Show system status")
            print("5. Open dashboard")
            print("6. Settings")
            print("7. Exit")
            print("="*50)
            
            try:
                choice = input("Enter your choice (1-7): ").strip()
                
                if choice == "1":
                    self._start_all_services()
                elif choice == "2":
                    self._stop_all_services()
                elif choice == "3":
                    self._restart_all_services()
                elif choice == "4":
                    self._show_system_status()
                elif choice == "5":
                    webbrowser.open("http://localhost:3000")
                elif choice == "6":
                    self._console_settings()
                elif choice == "7":
                    self._quit_application()
                else:
                    print("Invalid choice!")
                    
            except KeyboardInterrupt:
                self._quit_application()
            except Exception as e:
                self._log(f"Console menu error: {e}", "ERROR")
    
    def _console_settings(self):
        """Console-based settings"""
        print("\n" + "="*30)
        print("Settings")
        print("="*30)
        print(f"1. Auto-start on boot: {self.config.auto_start_on_boot}")
        print(f"2. Browser auto-open: {self.config.browser_auto_open}")
        print(f"3. Health check interval: {self.config.check_health_interval}s")
        print("4. Create desktop shortcut")
        print("5. Back to main menu")
        
        choice = input("Enter your choice (1-5): ").strip()
        
        if choice == "1":
            self.config.auto_start_on_boot = not self.config.auto_start_on_boot
            self.setup_auto_start(self.config.auto_start_on_boot)
            self._save_config()
            print(f"Auto-start {'enabled' if self.config.auto_start_on_boot else 'disabled'}")
            
        elif choice == "2":
            self.config.browser_auto_open = not self.config.browser_auto_open
            self._save_config()
            print(f"Browser auto-open {'enabled' if self.config.browser_auto_open else 'disabled'}")
            
        elif choice == "3":
            try:
                interval = int(input(f"Enter new interval (current: {self.config.check_health_interval}s): "))
                if 10 <= interval <= 300:
                    self.config.check_health_interval = interval
                    self._save_config()
                    print(f"Health check interval set to {interval}s")
                else:
                    print("Interval must be between 10 and 300 seconds")
            except ValueError:
                print("Invalid number")
                
        elif choice == "4":
            self.create_desktop_shortcut()


if __name__ == "__main__":
    launcher = EnhancedDesktopLauncher()
    launcher.run()