from dataclasses import dataclass
from typing import Set
from pathlib import Path

@dataclass
class AnalyzerConfig:
    # File types to analyze
    SUPPORTED_EXTENSIONS: Set[str] = {
        '.js', '.jsx', '.ts', '.tsx',
        '.css', '.scss', '.json',
        '.html', '.md', '.env.example'
    }
    
    # Directories to ignore
    IGNORE_DIRS: Set[str] = {
        'node_modules', '.next', '.git',
        'public', 'out', 'build', 'dist',
        '.cache', 'coverage', '.vscode'
    }
    
    # Files to ignore
    IGNORE_FILES: Set[str] = {
        '.DS_Store', 'package-lock.json',
        'yarn.lock', '.gitignore'
    }
    
    # Cache settings
    CACHE_DIR: Path = Path(".cache")
    CACHE_EXPIRY_HOURS: int = 24
    MAX_CACHE_SIZE_MB: int = 1024
    
    # Analysis settings
    MAX_FILE_SIZE_MB: int = 10
    BATCH_SIZE: int = 10
    PARALLEL_PROCESSES: int = 4
    
    # Ollama settings
    DEFAULT_MODEL: str = "llama2"
    API_TIMEOUT: int = 30
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 1