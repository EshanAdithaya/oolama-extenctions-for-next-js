# main.py
import tkinter as tk
import logging
from pathlib import Path
import sys
import os

# Add the src directory to Python path 
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.append(str(src_dir))

from src.gui.main_window import APIGeneratorGUI
from src.config.analyzer_config import AnalyzerConfig

def setup_environment():
    """Setup necessary directories and environment"""
    base_dir = Path(__file__).parent
    for directory in ['logs', 'templates', 'generated']:
        (base_dir / directory).mkdir(exist_ok=True)
        
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(base_dir / 'logs' / 'app.log'),
            logging.StreamHandler()
        ]
    )

def main():
    setup_environment()
    
    root = tk.Tk()
    app = APIGeneratorGUI(root)
    
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()