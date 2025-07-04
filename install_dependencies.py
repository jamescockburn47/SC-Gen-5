#!/usr/bin/env python3
"""
Installation script for SC Gen 5 dependencies
"""

import subprocess
import sys
import platform
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"Installing {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install {description}: {e}")
        print(f"Error output: {e.stderr}")
        return False

def install_python_dependencies():
    """Install Python dependencies"""
    print("Installing Python dependencies...")
    
    # Core dependencies
    core_deps = [
        "fastapi>=0.104.1",
        "uvicorn[standard]>=0.24.0",
        "streamlit>=1.28.0",
        "sentence-transformers>=2.2.2",
        "faiss-cpu>=1.7.4",
        "PyPDF2>=3.0.1",
        "pdf2image>=1.16.3",
        "pytesseract>=0.3.10",
        "Pillow>=10.0.1",
        "requests>=2.31.0",
        "python-multipart>=0.0.6",
        "python-dotenv>=1.0.0",
        "openai>=1.3.0",
        "google-generativeai>=0.3.0",
        "anthropic>=0.7.0",
        "numpy>=1.24.0",
        "pandas>=2.0.0",
        "pydantic>=2.4.0",
        "tiktoken>=0.5.0"
    ]
    
    # Enhanced OCR dependencies
    ocr_deps = [
        "paddlepaddle-cpu>=2.5.2",
        "paddleocr>=2.7.0",
        "FlagEmbedding>=1.2.0",
        "opencv-python>=4.8.0"
    ]
    
    # Desktop launcher dependencies
    launcher_deps = [
        "psutil>=5.9.0",
        "pystray>=0.19.0",
        "matplotlib>=3.6.0",
        "plotly>=5.15.0",
        "GPUtil>=1.4.0",
        "pynvml>=11.5.0"
    ]
    
    # Development dependencies
    dev_deps = [
        "pytest>=7.4.0",
        "pytest-asyncio>=0.21.0",
        "pytest-cov>=4.1.0",
        "black>=23.0.0",
        "ruff>=0.1.0",
        "mypy>=1.6.0",
        "types-requests>=2.31.0"
    ]
    
    # Platform-specific dependencies
    if platform.system() == "Windows":
        launcher_deps.extend([
            "pywin32>=305",
            "winshell>=0.6"
        ])
    elif platform.system() == "Linux":
        launcher_deps.append("python-xlib>=0.33")
    
    # Install all dependencies
    all_deps = core_deps + ocr_deps + launcher_deps + dev_deps
    
    for dep in all_deps:
        if not run_command(f"{sys.executable} -m pip install {dep}", dep):
            print(f"⚠️ Warning: Failed to install {dep}")
    
    print("✅ Python dependencies installation completed")

def install_node_dependencies():
    """Install Node.js dependencies"""
    print("\nInstalling Node.js dependencies...")
    
    # Frontend dependencies
    frontend_dir = Path("frontend")
    if frontend_dir.exists():
        print("Installing frontend dependencies...")
        if not run_command("npm install", "Frontend dependencies"):
            print("⚠️ Warning: Failed to install frontend dependencies")
    else:
        print("⚠️ Frontend directory not found")
    
    # Terminal server dependencies
    terminal_dir = Path("terminal-server")
    if terminal_dir.exists():
        print("Installing terminal server dependencies...")
        if not run_command("npm install", "Terminal server dependencies"):
            print("⚠️ Warning: Failed to install terminal server dependencies")
    else:
        print("⚠️ Terminal server directory not found")

def install_system_dependencies():
    """Install system dependencies"""
    print("\nChecking system dependencies...")
    
    if platform.system() == "Windows":
        print("Windows detected - no additional system dependencies needed")
        
    elif platform.system() == "Linux":
        print("Linux detected - installing system dependencies...")
        
        # Ubuntu/Debian
        if Path("/etc/debian_version").exists():
            deps = [
                "tesseract-ocr",
                "tesseract-ocr-eng",
                "ghostscript",
                "poppler-utils",
                "libgl1-mesa-glx",
                "libglib2.0-0"
            ]
            
            for dep in deps:
                run_command(f"sudo apt-get install -y {dep}", f"System package {dep}")
        
        # CentOS/RHEL/Fedora
        elif Path("/etc/redhat-release").exists():
            deps = [
                "tesseract",
                "tesseract-langpack-eng",
                "ghostscript",
                "poppler-utils",
                "mesa-libGL",
                "glib2"
            ]
            
            for dep in deps:
                run_command(f"sudo yum install -y {dep}", f"System package {dep}")
        
        else:
            print("⚠️ Unsupported Linux distribution - please install tesseract-ocr manually")
    
    elif platform.system() == "Darwin":  # macOS
        print("macOS detected - installing system dependencies...")
        run_command("brew install tesseract tesseract-lang", "Tesseract OCR")
        run_command("brew install ghostscript poppler", "PDF tools")

def verify_installation():
    """Verify that key dependencies are working"""
    print("\nVerifying installation...")
    
    # Test Python imports
    test_imports = [
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn"),
        ("paddleocr", "PaddleOCR"),
        ("cv2", "OpenCV"),
        ("psutil", "psutil"),
        ("pystray", "pystray"),
        ("plotly", "plotly"),
        ("matplotlib", "matplotlib")
    ]
    
    if platform.system() == "Windows":
        test_imports.extend([
            ("win32com.client", "pywin32"),
            ("winshell", "winshell")
        ])
    
    for module, name in test_imports:
        try:
            __import__(module)
            print(f"✅ {name} imported successfully")
        except ImportError:
            print(f"❌ {name} import failed")
    
    # Test Node.js
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        print(f"✅ Node.js {result.stdout.strip()}")
    except:
        print("❌ Node.js not found")
    
    try:
        result = subprocess.run(["npm", "--version"], capture_output=True, text=True)
        print(f"✅ npm {result.stdout.strip()}")
    except:
        print("❌ npm not found")

def main():
    """Main installation function"""
    print("SC Gen 5 - Dependency Installation")
    print("=" * 40)
    
    # Check Python version
    if sys.version_info < (3, 11):
        print("❌ Python 3.11+ required")
        sys.exit(1)
    
    print(f"✅ Python {sys.version}")
    
    # Install dependencies
    install_python_dependencies()
    install_node_dependencies()
    install_system_dependencies()
    
    # Verify installation
    verify_installation()
    
    print("\n" + "=" * 40)
    print("Installation completed!")
    print("\nNext steps:")
    print("1. Run: python test_shortcut.py")
    print("2. Run: python desktop_launcher.py")
    print("3. Check the desktop for the SC Gen 5 shortcut")

if __name__ == "__main__":
    main() 