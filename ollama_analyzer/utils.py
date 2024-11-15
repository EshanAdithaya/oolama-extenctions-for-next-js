import os
from pathlib import Path
from typing import List, Dict, Set
from config import AnalyzerConfig
import logging

logger = logging.getLogger('FileScanner')

def format_size(size_in_bytes: int) -> str:
    """Convert bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_in_bytes < 1024:
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024
    return f"{size_in_bytes:.2f} TB"

def validate_project_path(project_path: Path) -> bool:
    """Validate if the path is a valid Next.js/React project directory"""
    logger.info(f"Validating project path: {project_path}")
    
    # Check if path exists and is a directory
    if not project_path.exists() or not project_path.is_dir():
        logger.error(f"Invalid path: {project_path}")
        return False
    
    logger.info("Directory structure:")
    for item in project_path.iterdir():
        logger.info(f"  {item.name} {'(dir)' if item.is_dir() else '(file)'}")
    
    return True

def get_actual_files(project_path: Path) -> List[str]:
    """Get all files in the project directory without filtering"""
    files = []
    
    logger.info(f"Scanning all files in: {project_path}")
    logger.info("Current directory structure:")
    
    # First, log the entire directory structure
    for root, dirs, filenames in os.walk(project_path):
        level = root.replace(str(project_path), '').count(os.sep)
        indent = ' ' * 4 * level
        logger.info(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 4 * (level + 1)
        for filename in filenames:
            logger.info(f"{subindent}{filename}")
            # Get path relative to project root
            full_path = Path(root) / filename
            try:
                relative_path = full_path.relative_to(project_path)
                files.append(str(relative_path))
            except Exception as e:
                logger.error(f"Error processing file {filename}: {e}")
    
    return sorted(files)

def get_directory_size(path: Path) -> int:
    """Calculate total size of a directory and its contents"""
    total_size = 0
    for dirpath, _, filenames in os.walk(path):
        for filename in filenames:
            file_path = Path(dirpath) / filename
            try:
                total_size += file_path.stat().st_size
            except Exception:
                continue
    return total_size

def get_project_files(project_path: Path, config: AnalyzerConfig) -> List[str]:
    """Get all project files with minimal filtering"""
    if not validate_project_path(project_path):
        logger.error("Invalid project path")
        return []
    
    logger.info(f"Starting project scan at: {project_path}")
    
    all_files = get_actual_files(project_path)
    logger.info(f"Found {len(all_files)} total files")
    
    # Only filter out node_modules and .git
    filtered_files = [
        f for f in all_files 
        if not any(part in str(f).split(os.sep) for part in ['node_modules', '.git'])
    ]
    
    logger.info(f"After minimal filtering: {len(filtered_files)} files")
    for file in filtered_files:
        logger.info(f"Including file: {file}")
    
    return filtered_files

def count_directories(path: Path, ignore_dirs: Set[str]) -> int:
    """Count number of directories excluding ignored ones"""
    count = 0
    for root, dirs, _ in os.walk(path):
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        count += len(dirs)
    return count

def analyze_project_structure(project_path: Path, config: AnalyzerConfig) -> Dict:
    """Analyze project structure with actual file system data"""
    logger.info(f"Starting analysis of: {project_path}")
    
    # Initialize statistics
    stats = {
        'total_size': 0,
        'total_dirs': 0,
        'total_files': 0,
        'by_extension': {},
        'by_directory': {},
        'directory_tree': {}
    }
    
    try:
        # Get all files
        files = get_project_files(project_path, config)
        stats['total_files'] = len(files)
        
        # Process each file
        for file_path in files:
            try:
                full_path = project_path / file_path
                if full_path.exists():
                    # Update size
                    file_size = full_path.stat().st_size
                    stats['total_size'] += file_size
                    
                    # Update extension stats
                    ext = full_path.suffix.lower()
                    stats['by_extension'][ext] = stats['by_extension'].get(ext, 0) + 1
                    
                    # Update directory stats
                    dir_path = str(Path(file_path).parent)
                    stats['by_directory'][dir_path] = stats['by_directory'].get(dir_path, 0) + 1
                    
            except Exception as e:
                logger.error(f"Error processing file {file_path}: {e}")
        
        # Count directories
        stats['total_dirs'] = count_directories(project_path, config.IGNORE_DIRS)
        
        logger.info(f"Analysis complete: {stats['total_files']} files in {stats['total_dirs']} directories")
        logger.info(f"Total size: {format_size(stats['total_size'])}")
        
        return {
            'stats': stats,
            'files': files
        }
        
    except Exception as e:
        logger.error(f"Error during analysis: {e}")
        raise