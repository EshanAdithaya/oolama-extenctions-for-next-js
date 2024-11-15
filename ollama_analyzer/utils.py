import os
from typing import List, Set
from pathlib import Path
from config import AnalyzerConfig

def get_project_files(project_path: Path, config: AnalyzerConfig) -> List[str]:
    """Get list of files to analyze based on configuration"""
    files = []
    
    for root, dirs, filenames in os.walk(project_path):
        # Remove ignored directories
        dirs[:] = [d for d in dirs if d not in config.IGNORE_DIRS]
        
        for filename in filenames:
            if filename in config.IGNORE_FILES:
                continue
                
            if any(filename.endswith(ext) for ext in config.SUPPORTED_EXTENSIONS):
                rel_path = os.path.relpath(os.path.join(root, filename), project_path)
                files.append(rel_path)
                
    return files

def format_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"