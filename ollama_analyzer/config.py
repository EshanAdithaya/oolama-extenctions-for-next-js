# config.py
from dataclasses import dataclass, field
from typing import Set
from pathlib import Path

def default_extensions() -> Set[str]:
    return {
        '.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs',
        '.css', '.scss', '.sass', '.less', '.module.css', '.module.scss',
        '.json', '.env', '.layout.tsx', '.layout.jsx', '.layout.js',
        '.md', '.mdx', '.txt'
    }

def default_ignore_dirs() -> Set[str]:
    return {
        'node_modules', '.next', '.git', 'out', 'build', 'dist',
        '.cache', 'coverage', '.vscode', '__pycache__', 'logs', 'tmp'
    }

def default_ignore_files() -> Set[str]:
    return {
        '.DS_Store', 'package-lock.json', 'yarn.lock', '.gitignore',
        '*.log', '*.map', 'thumbs.db'
    }

@dataclass
class AnalyzerConfig:
    SUPPORTED_EXTENSIONS: Set[str] = field(default_factory=default_extensions)
    IGNORE_DIRS: Set[str] = field(default_factory=default_ignore_dirs)
    IGNORE_FILES: Set[str] = field(default_factory=default_ignore_files)
    CACHE_DIR: Path = field(default_factory=lambda: Path(".cache"))
    CACHE_EXPIRY_HOURS: int = 24
    MAX_CACHE_SIZE_MB: int = 1024
    MAX_FILE_SIZE_MB: int = 10
    BATCH_SIZE: int = 10
    PARALLEL_PROCESSES: int = 4
    DEFAULT_MODEL: str = "llama3.2"
    API_TIMEOUT: int = 30
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 1