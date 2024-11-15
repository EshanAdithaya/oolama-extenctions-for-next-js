import tkinter as tk
import logging
from pathlib import Path
import time
from gui import OllamaAnalyzerGUI

def main():
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('ollama_analyzer.log'),
            logging.StreamHandler()
        ]
    )

    # Create required directories
    Path('logs').mkdir(exist_ok=True)
    Path('analysis_results').mkdir(exist_ok=True)

    # Initialize GUI
    root = tk.Tk()
    app = OllamaAnalyzerGUI(root)

    # Add window close handler
    def on_closing():
        if app.is_analyzing:
            app.is_analyzing = False
            time.sleep(1)
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()