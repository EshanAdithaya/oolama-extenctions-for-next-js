import tkinter as tk
import logging
from pathlib import Path
import time
from gui import OllamaAnalyzerGUI

def main():
    # Configure root logger
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('debug.log'),
            logging.StreamHandler()
        ]
    )

    # Create required directories
    Path('logs').mkdir(exist_ok=True)
    Path('analysis_results').mkdir(exist_ok=True)

    # Initialize GUI
    root = tk.Tk()
    app = OllamaAnalyzerGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()