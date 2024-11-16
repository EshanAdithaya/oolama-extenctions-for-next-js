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
    API_TIMEOUT: int = 60
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 1
    
    # Output structure configuration
    GENERATE_SERVICES: bool = True
    GENERATE_DTOS: bool = True
    GENERATE_CONTROLLERS: bool = True
    GENERATE_SWAGGER: bool = True
    
    # Template paths
    TEMPLATE_DIR: Path = field(default_factory=lambda: Path("templates"))
    
    # Ollama configuration
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama2"  # Default model
    
    # Additional settings
    DEBUG_MODE: bool = False
    LOG_LEVEL: str = "INFO"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary with JSON-serializable values"""
        return {
            'ENTITY_PATTERNS': list(self.ENTITY_PATTERNS),
            'IGNORE_DIRS': list(self.IGNORE_DIRS),
            'CACHE_DIR': str(self.CACHE_DIR),
            'API_TIMEOUT': self.API_TIMEOUT,
            'MAX_RETRIES': self.MAX_RETRIES,
            'RETRY_DELAY': self.RETRY_DELAY,
            'GENERATE_SERVICES': self.GENERATE_SERVICES,
            'GENERATE_DTOS': self.GENERATE_DTOS,
            'GENERATE_CONTROLLERS': self.GENERATE_CONTROLLERS,
            'GENERATE_SWAGGER': self.GENERATE_SWAGGER,
            'TEMPLATE_DIR': str(self.TEMPLATE_DIR),
            'OLLAMA_BASE_URL': self.OLLAMA_BASE_URL,
            'OLLAMA_MODEL': self.OLLAMA_MODEL,
            'DEBUG_MODE': self.DEBUG_MODE,
            'LOG_LEVEL': self.LOG_LEVEL
        }
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'AnalyzerConfig':
        """Create config instance from dictionary"""
        # Convert lists back to sets for patterns and ignore dirs
        if 'ENTITY_PATTERNS' in config_dict:
            config_dict['ENTITY_PATTERNS'] = set(config_dict['ENTITY_PATTERNS'])
        if 'IGNORE_DIRS' in config_dict:
            config_dict['IGNORE_DIRS'] = set(config_dict['IGNORE_DIRS'])
        
        # Convert string paths back to Path objects
        if 'CACHE_DIR' in config_dict:
            config_dict['CACHE_DIR'] = Path(config_dict['CACHE_DIR'])
        if 'TEMPLATE_DIR' in config_dict:
            config_dict['TEMPLATE_DIR'] = Path(config_dict['TEMPLATE_DIR'])
        
        return cls(**config_dict)

    def validate(self) -> bool:
        """Validate configuration settings"""
        try:
            # Check if paths exist or can be created
            self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
            self.TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)
            
            # Validate URL format
            if not self.OLLAMA_BASE_URL.startswith(('http://', 'https://')):
                raise ValueError("OLLAMA_BASE_URL must start with http:// or https://")
            
            # Validate timeout and retry settings
            if self.API_TIMEOUT <= 0:
                raise ValueError("API_TIMEOUT must be greater than 0")
            if self.MAX_RETRIES < 0:
                raise ValueError("MAX_RETRIES cannot be negative")
            if self.RETRY_DELAY <= 0:
                raise ValueError("RETRY_DELAY must be greater than 0")
            
            return True
            
        except Exception as e:
            print(f"Configuration validation failed: {str(e)}")
            return False