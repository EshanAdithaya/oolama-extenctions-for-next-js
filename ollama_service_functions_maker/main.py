import tkinter as tk
import logging
from pathlib import Path
import sys
import os
from src.config.analyzer_config import AnalyzerConfig

# Add the src directory to Python path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.append(str(src_dir))

from src.gui.main_window import APIGeneratorGUI
from src.config.analyzer_config import AnalyzerConfig

def setup_environment():
    """Setup necessary directories and environment"""
    # Create required directories
    base_dir = Path(__file__).parent
    for directory in ['logs', 'templates', 'generated']:
        (base_dir / directory).mkdir(exist_ok=True)
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(base_dir / 'logs' / 'app.log'),
            logging.StreamHandler()
        ]
    )

def check_dependencies():
    """Check if all required dependencies are installed"""
    required_packages = ['requests', 'jinja2']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("Missing dependencies:", ", ".join(missing_packages))
        print("Please install required dependencies:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    return True

def main():
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)

    # Setup environment
    setup_environment()

    # Create and run GUI
    root = tk.Tk()
    app = APIGeneratorGUI(root)
    
    # Handle window close
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # Start application
    root.mainloop()

if __name__ == "__main__":
    main()  