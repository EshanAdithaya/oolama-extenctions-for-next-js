from dataclasses import dataclass, field
from typing import Set, Dict, Any
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