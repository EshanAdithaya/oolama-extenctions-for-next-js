from dataclasses import dataclass, field
from typing import Set
from pathlib import Path

def default_extensions() -> Set[str]:
    return {
        # JavaScript/TypeScript
        '.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs',
        
        # Styles
        '.css', '.scss', '.sass', '.less', 
        '.module.css', '.module.scss', '.module.sass', '.module.less',
        '.styled.js', '.styled.ts',
        
        # Next.js/React specific
        '.page.tsx', '.page.jsx', '.page.js',
        '.layout.tsx', '.layout.jsx', '.layout.js',
        '.component.tsx', '.component.jsx', '.component.js',
        
        # Component files
        '.form.tsx', '.form.jsx', '.form.js',
        '.view.tsx', '.view.jsx', '.view.js',
        '.modal.tsx', '.modal.jsx', '.modal.js',
        '.dialog.tsx', '.dialog.jsx', '.dialog.js',
        
        # Utility files
        '.util.ts', '.util.js',
        '.helper.ts', '.helper.js',
        '.service.ts', '.service.js',
        '.hook.ts', '.hook.js',
        '.context.ts', '.context.js',
        '.provider.ts', '.provider.js',
        
        # Config and data files
        '.json', '.env', '.env.local', '.env.development', '.env.production',
        '.config.js', '.config.ts',
        
        # Documentation
        '.md', '.mdx', '.txt',
        
        # Type definitions
        '.d.ts'
    }

def default_ignore_dirs() -> Set[str]:
    return {
        'node_modules', '.next', '.git', 'out', 'build', 'dist',
        '.cache', 'coverage', '.vscode', '__pycache__', 'logs', 'tmp',
        '.husky', '.github', '.storybook', '__tests__', '__mocks__',
        'e2e', 'cypress', 'jest', 'test-utils'
    }

def default_ignore_files() -> Set[str]:
    return {
        '.DS_Store', 'package-lock.json', 'yarn.lock', '.gitignore',
        '*.log', '*.map', 'thumbs.db', 
        '*.test.js', '*.spec.js', '*.test.tsx', '*.spec.tsx',
        '*.test.jsx', '*.spec.jsx', '*.stories.tsx', '*.stories.jsx',
        '*.min.js', '*.min.css', '*.bundle.js', '*.bundle.css',
        'jest.config.*', 'babel.config.*', 'tsconfig.tsbuildinfo'
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
    DEFAULT_MODEL: str = "llama2"
    API_TIMEOUT: int = 30
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 1