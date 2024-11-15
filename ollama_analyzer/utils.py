import os
from typing import List, Set, Dict
from pathlib import Path
import fnmatch
from config import AnalyzerConfig

def get_project_files(project_path: Path, config: AnalyzerConfig) -> List[str]:
    """Get all project files recursively, excluding ignored patterns"""
    files = []
    
    def is_valid_file(file_path: str) -> bool:
        # Check if file should be ignored
        basename = os.path.basename(file_path)
        if any(fnmatch.fnmatch(basename, pattern) for pattern in config.IGNORE_FILES):
            return False
            
        # Check file extension
        ext = ''.join(Path(file_path).suffixes)  # Handle multiple extensions like .module.css
        return any(ext.endswith(supported_ext) for supported_ext in config.SUPPORTED_EXTENSIONS)

    def scan_directory(current_path: Path):
        try:
            for entry in os.scandir(current_path):
                relative_path = Path(entry.path).relative_to(project_path)
                
                # Skip ignored directories
                if entry.is_dir():
                    if entry.name in config.IGNORE_DIRS:
                        continue
                    scan_directory(entry.path)
                    continue
                
                # Process file
                if entry.is_file() and is_valid_file(entry.path):
                    files.append(str(relative_path).replace(os.sep, '/'))
                    
        except Exception as e:
            print(f"Error scanning directory {current_path}: {str(e)}")
            
    scan_directory(project_path)
    return sorted(files)

def get_directory_structure(project_path: Path, config: AnalyzerConfig) -> Dict:
    """Generate complete directory structure excluding ignored patterns"""
    structure = {}
    
    def scan_dir(current_path: Path, current_dict: Dict):
        try:
            for entry in os.scandir(current_path):
                if entry.is_dir():
                    if entry.name in config.IGNORE_DIRS:
                        continue
                    current_dict[entry.name] = {}
                    scan_dir(entry.path, current_dict[entry.name])
                elif entry.is_file():
                    if not any(fnmatch.fnmatch(entry.name, pattern) 
                             for pattern in config.IGNORE_FILES):
                        current_dict[entry.name] = None
        except Exception as e:
            print(f"Error scanning directory {current_path}: {str(e)}")
            
    scan_dir(project_path, structure)
    return structure

def analyze_project_structure(project_path: Path, config: AnalyzerConfig) -> Dict:
    """Analyze project structure and return detailed information"""
    structure = {
        'files': [],
        'directories': set(),
        'file_types': {},
        'structure_tree': {},
        'stats': {
            'total_files': 0,
            'total_dirs': 0,
            'total_size': 0
        }
    }
    
    def process_directory(current_path: Path):
        try:
            for entry in os.scandir(current_path):
                relative_path = Path(entry.path).relative_to(project_path)
                
                if entry.is_dir():
                    if entry.name in config.IGNORE_DIRS:
                        continue
                    structure['directories'].add(str(relative_path))
                    structure['stats']['total_dirs'] += 1
                    process_directory(entry.path)
                    
                elif entry.is_file():
                    if any(fnmatch.fnmatch(entry.name, pattern) 
                          for pattern in config.IGNORE_FILES):
                        continue
                        
                    file_path = str(relative_path).replace(os.sep, '/')
                    ext = ''.join(Path(entry.name).suffixes)
                    
                    if any(ext.endswith(supported_ext) 
                          for supported_ext in config.SUPPORTED_EXTENSIONS):
                        structure['files'].append(file_path)
                        structure['stats']['total_files'] += 1
                        structure['stats']['total_size'] += entry.stat().st_size
                        structure['file_types'][ext] = structure['file_types'].get(ext, 0) + 1
                        
        except Exception as e:
            print(f"Error processing directory {current_path}: {str(e)}")
    
    process_directory(project_path)
    structure['structure_tree'] = get_directory_structure(project_path, config)
    return structure

def format_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"