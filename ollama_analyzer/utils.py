import os
from pathlib import Path
from typing import List, Dict, Set
from config import AnalyzerConfig
import fnmatch

def format_size(size_in_bytes: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_in_bytes < 1024:
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024
    return f"{size_in_bytes:.2f} TB"

def is_supported_file(file_path: Path, config: AnalyzerConfig) -> bool:
    """Enhanced check for supported files including deeply nested ones"""
    # Get the file extension
    ext = file_path.suffix.lower()
    file_name = file_path.name.lower()
    
    # Check common Next.js/React patterns
    next_patterns = [
        '.page.', '.layout.', '.component.',
        'form.', 'view.', 'modal.',
        'sidebar.', 'header.', 'footer.',
        'nav.', 'menu.', 'list.',
        'item.', 'card.', 'button.',
        'input.', 'select.', 'table.',
        'dialog.', 'popup.', 'toast.',
        'provider.', 'context.', 'hook.',
        'utils.', 'helper.', 'service.',
        'api.', 'client.', 'server.',
        'styles.', 'theme.', 'config.'
    ]

    # Direct extension match
    if ext in config.SUPPORTED_EXTENSIONS:
        return True
        
    # Pattern matching for Next.js/React files
    if any(pattern in file_name for pattern in next_patterns):
        return True

    # Check for TypeScript definition files
    if file_name.endswith('.d.ts'):
        return True

    return False

def should_ignore_path(path: Path, config: AnalyzerConfig) -> bool:
    """Enhanced ignore check for nested paths"""
    # Convert path to string for pattern matching
    path_str = str(path)
    
    # Check for ignored directories anywhere in the path
    for ignore_dir in config.IGNORE_DIRS:
        if f"/{ignore_dir}/" in path_str.replace("\\", "/"):
            return True
            
    # Check filename against ignore patterns
    file_name = path.name
    for pattern in config.IGNORE_FILES:
        if pattern.startswith('*'):
            if fnmatch.fnmatch(file_name, pattern):
                return True
        elif pattern == file_name:
            return True
            
    # Additional checks for common test and generated files
    test_patterns = [
        '*.test.*', '*.spec.*', '*.stories.*',
        '__tests__/*', '__mocks__/*',
        '*.min.*', '*.bundle.*'
    ]
    
    for pattern in test_patterns:
        if fnmatch.fnmatch(path_str, pattern):
            return True
            
    return False

def get_project_files(project_path: Path, config: AnalyzerConfig) -> List[str]:
    """Enhanced recursive file scanning with detailed logging"""
    files = []
    scanned_dirs = set()
    
    def scan_directory(current_path: Path, depth: int = 0):
        """Recursive directory scanner"""
        try:
            # Avoid infinite recursion
            if str(current_path) in scanned_dirs:
                return
            scanned_dirs.add(str(current_path))
            
            # Scan all items in directory
            for item in current_path.iterdir():
                try:
                    # Get relative path
                    relative_path = item.relative_to(project_path)
                    
                    if item.is_dir():
                        # Skip ignored directories
                        if item.name not in config.IGNORE_DIRS:
                            scan_directory(item, depth + 1)
                    else:
                        # Process file
                        if not should_ignore_path(relative_path, config):
                            if is_supported_file(item, config):
                                if item.stat().st_size <= (config.MAX_FILE_SIZE_MB * 1024 * 1024):
                                    files.append(str(relative_path))
                                    print(f"Found file: {relative_path}")
                                
                except Exception as e:
                    print(f"Error processing {item}: {str(e)}")
                    
        except Exception as e:
            print(f"Error scanning directory {current_path}: {str(e)}")
            
    # Start recursive scan
    scan_directory(project_path)
    return sorted(files)

def analyze_project_structure(project_path: Path, config: AnalyzerConfig) -> Dict:
    """Enhanced project structure analysis with nested directory support"""
    stats = {
        'total_size': 0,
        'total_dirs': 0,
        'total_files': 0,
        'by_extension': {},
        'by_directory': {},
        'nested_depth': {},
        'file_types': {
            'components': 0,
            'pages': 0,
            'layouts': 0,
            'hooks': 0,
            'utils': 0,
            'styles': 0,
            'config': 0,
            'other': 0
        }
    }
    
    files = []
    
    def categorize_file(file_path: Path):
        """Categorize file based on its path and name"""
        path_str = str(file_path).lower()
        if 'components' in path_str:
            stats['file_types']['components'] += 1
        elif 'pages' in path_str:
            stats['file_types']['pages'] += 1
        elif 'layouts' in path_str:
            stats['file_types']['layouts'] += 1
        elif 'hooks' in path_str:
            stats['file_types']['hooks'] += 1
        elif 'utils' in path_str:
            stats['file_types']['utils'] += 1
        elif any(ext in path_str for ext in ['.css', '.scss', '.sass', '.less']):
            stats['file_types']['styles'] += 1
        elif 'config' in path_str:
            stats['file_types']['config'] += 1
        else:
            stats['file_types']['other'] += 1
    
    def process_directory(current_path: Path, depth: int = 0):
        """Recursive directory processor"""
        try:
            stats['total_dirs'] += 1
            stats['nested_depth'][depth] = stats['nested_depth'].get(depth, 0) + 1
            
            for item in current_path.iterdir():
                try:
                    relative_path = item.relative_to(project_path)
                    
                    if item.is_dir():
                        if item.name not in config.IGNORE_DIRS:
                            process_directory(item, depth + 1)
                    else:
                        if not should_ignore_path(relative_path, config):
                            if is_supported_file(item, config):
                                file_size = item.stat().st_size
                                if file_size <= (config.MAX_FILE_SIZE_MB * 1024 * 1024):
                                    # Add to files list
                                    files.append(str(relative_path))
                                    
                                    # Update statistics
                                    stats['total_size'] += file_size
                                    stats['total_files'] += 1
                                    
                                    # Track by extension
                                    ext = item.suffix
                                    stats['by_extension'][ext] = stats['by_extension'].get(ext, 0) + 1
                                    
                                    # Track by directory
                                    dir_path = str(relative_path.parent)
                                    stats['by_directory'][dir_path] = stats['by_directory'].get(dir_path, 0) + 1
                                    
                                    # Categorize file
                                    categorize_file(relative_path)
                                    
                except Exception as e:
                    print(f"Error processing {item}: {str(e)}")
                    
        except Exception as e:
            print(f"Error analyzing directory {current_path}: {str(e)}")
            
    # Start recursive analysis
    process_directory(project_path)
    
    return {
        'stats': stats,
        'files': sorted(files)
    }