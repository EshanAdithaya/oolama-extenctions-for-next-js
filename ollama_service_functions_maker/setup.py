import os
from pathlib import Path

def create_project_structure():
    # Define base directory
    base_dir = Path("ollama_service_functions_maker")
    
    # Create main directories
    directories = [
        "src",
        "src/config",
        "src/generators",
        "src/gui",
        "src/utils",
        "logs",
        "templates",
        "generated"
    ]
    
    for dir_path in directories:
        (base_dir / dir_path).mkdir(parents=True, exist_ok=True)
        
        # Create __init__.py in each src directory
        if dir_path.startswith('src'):
            init_file = base_dir / dir_path / "__init__.py"
            init_file.touch(exist_ok=True)

    # Create main configuration files
    create_analyzer_config(base_dir / "src/config/analyzer_config.py")
    create_code_generator(base_dir / "src/generators/code_generator.py")
    create_entity_analyzer(base_dir / "src/generators/entity_analyzer.py")
    create_main_window(base_dir / "src/gui/main_window.py")
    create_ollama_utils(base_dir / "src/utils/ollama_utils.py")
    create_main_file(base_dir / "main.py")

def create_analyzer_config(file_path):
    content = '''
from dataclasses import dataclass, field
from typing import Set
from pathlib import Path

def default_entity_patterns() -> Set[str]:
    return {
        '.entity.ts',
        '.model.ts',
        'entity.interface.ts',
        'model.interface.ts'
    }

def default_ignore_dirs() -> Set[str]:
    return {
        'node_modules',
        '.next',
        'dist',
        'build',
        'coverage',
        '__tests__'
    }

@dataclass
class AnalyzerConfig:
    """Configuration class for the API Generator"""
    
    # File patterns and directories
    ENTITY_PATTERNS: Set[str] = field(default_factory=default_entity_patterns)
    IGNORE_DIRS: Set[str] = field(default_factory=default_ignore_dirs)
    CACHE_DIR: Path = field(default_factory=lambda: Path(".cache"))
    
    # API configuration
    API_TIMEOUT: int = 120
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 2
    
    # Output structure configuration
    GENERATE_SERVICES: bool = True
    GENERATE_DTOS: bool = True
    GENERATE_CONTROLLERS: bool = True
    GENERATE_SWAGGER: bool = True
    
    # Template paths
    TEMPLATE_DIR: Path = field(default_factory=lambda: Path("templates"))
    
    # Ollama configuration
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "codellama"
'''
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content.strip())

def create_code_generator(file_path):
    content = '''
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Any, Tuple, Union
from pathlib import Path
import logging
import json
import re
import requests
import time
from time import sleep
import os

@dataclass
class CodeGenerationConfig:
    """Configuration for code generation"""
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "codellama"
    API_TIMEOUT: int = 120
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 2
    TEMPLATE_DIR: Path = Path("templates")
    CACHE_DIR: Path = Path(".cache")

class SmartCodeGenerator:
    """Main code generation orchestrator"""
    
    def __init__(self, config: CodeGenerationConfig):
        self.config = config
        self.logger = logging.getLogger('SmartCodeGenerator')
        self.project_context = {}

    def analyze_project_structure(self, source_path: Path):
        """Analyze project structure"""
        self.logger.info(f"Analyzing project structure at {source_path}")
        try:
            # Implementation here
            pass
        except Exception as e:
            self.logger.error(f"Error analyzing project: {str(e)}")
            raise
'''
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content.strip())

def create_entity_analyzer(file_path):
    content = '''
import re
from typing import Dict, List, Optional
from pathlib import Path
import logging

class EntityAnalyzer:
    def __init__(self):
        self.logger = logging.getLogger('EntityAnalyzer')
    
    def analyze_entity_file(self, file_path: Path) -> Optional[Dict]:
        """Analyze a TypeScript entity file and extract its structure"""
        try:
            # Implementation here
            pass
        except Exception as e:
            self.logger.error(f"Error analyzing entity file {file_path}: {str(e)}")
            return None
'''
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content.strip())

def create_main_window(file_path):
    content = '''
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import logging
from pathlib import Path
import json
import threading
import time
import requests
import os

from src.generators.code_generator import SmartCodeGenerator
from src.config.analyzer_config import AnalyzerConfig
from src.generators.entity_analyzer import EntityAnalyzer

class APIGeneratorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Next.js API Generator")
        self.root.geometry("1200x800")
        
        # Initialize components
        self.config = AnalyzerConfig()
        self.entity_analyzer = EntityAnalyzer()
        self.code_generator = SmartCodeGenerator(self.config)
        
        # Initialize variables
        self.source_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.is_connected = False
        
        # Create GUI elements
        self.create_widgets()
        
    def create_widgets(self):
        # Implement GUI widgets here
        pass

    def on_closing(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.root.destroy()
'''
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content.strip())

def create_ollama_utils(file_path):
    content = '''
import subprocess
import platform
import requests
from typing import Tuple
import logging

def check_ollama_installation() -> Tuple[bool, str]:
    """Check if Ollama is installed"""
    try:
        result = subprocess.run(['ollama', '--version'], 
                              capture_output=True, 
                              text=True)
        if result.returncode == 0:
            return True, result.stdout.strip()
        return False, "Ollama not found"
    except Exception as e:
        return False, str(e)
'''
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content.strip())

def create_main_file(file_path):
    content = '''
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
'''
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content.strip())

if __name__ == "__main__":
    create_project_structure()
    print("Project structure created successfully!")