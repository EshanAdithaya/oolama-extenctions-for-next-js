import os
from pathlib import Path
from typing import List, Dict, Set
from config import AnalyzerConfig
import logging

logger = logging.getLogger('FileScanner')

def format_size(size_in_bytes: float) -> str:
    """Convert bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_in_bytes < 1024.0:
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024.0
    return f"{size_in_bytes:.2f} TB"

def scan_directory_structure(directory: Path, indent: str = "") -> None:
    """Debug function to print actual directory structure"""
    try:
        for item in directory.iterdir():
            if item.is_file():
                logger.debug(f"{indent}FILE: {item.name}")
            elif item.is_dir():
                logger.debug(f"{indent}DIR: {item.name}/")
                scan_directory_structure(item, indent + "  ")
    except Exception as e:
        logger.error(f"Error scanning directory {directory}: {e}")

def get_project_files(project_path: Path, config: AnalyzerConfig) -> List[str]:
    """Enhanced recursive file scanning with detailed logging"""
    files = []
    logger.info(f"Starting deep scan of project at: {project_path}")
    
    # First, log the complete directory structure for debugging
    logger.debug("Full directory structure:")
    scan_directory_structure(project_path)
    
    def process_directory(current_path: Path) -> None:
        """Recursive function to process directories"""
        try:
            for item in current_path.iterdir():
                relative_path = item.relative_to(project_path)
                
                if item.is_dir():
                    # Log directory discovery
                    logger.debug(f"Scanning directory: {relative_path}")
                    
                    # Skip ignored directories
                    if item.name in config.IGNORE_DIRS:
                        logger.debug(f"Skipping ignored directory: {relative_path}")
                        continue
                        
                    # Recursively process subdirectory
                    process_directory(item)
                else:
                    # Log file discovery
                    logger.debug(f"Found file: {relative_path}")
                    
                    # Check file extension
                    if item.suffix.lower() in config.SUPPORTED_EXTENSIONS:
                        # Check file size
                        try:
                            file_size = item.stat().st_size
                            if file_size <= (config.MAX_FILE_SIZE_MB * 1024 * 1024):
                                logger.info(f"Including file: {relative_path} (size: {format_size(file_size)})")
                                files.append(str(relative_path))
                            else:
                                logger.warning(f"File too large, skipping: {relative_path} (size: {format_size(file_size)})")
                        except Exception as e:
                            logger.error(f"Error checking file size for {relative_path}: {e}")
                    else:
                        logger.debug(f"Skipping unsupported file type: {relative_path}")
                        
        except Exception as e:
            logger.error(f"Error processing directory {current_path}: {e}")
    
    # Start the recursive scan
    process_directory(project_path)
    
    # Log summary
    logger.info(f"Scan complete. Found {len(files)} files")
    logger.info("Files by extension:")
    extension_count = {}
    for file in files:
        ext = Path(file).suffix.lower()
        extension_count[ext] = extension_count.get(ext, 0) + 1
    for ext, count in extension_count.items():
        logger.info(f"  {ext}: {count} files")
    
    return sorted(files)

def analyze_project_structure(project_path: Path, config: AnalyzerConfig) -> Dict:
    """Enhanced project structure analysis with detailed directory info"""
    logger.info(f"Starting project analysis at: {project_path}")
    
    stats = {
        'total_size': 0,
        'total_dirs': 0,
        'total_files': 0,
        'by_extension': {},
        'by_directory': {},
        'directory_tree': {},
        'max_depth': 0
    }
    
    def analyze_directory(current_path: Path, depth: int = 0) -> None:
        """Recursive directory analyzer"""
        nonlocal stats
        
        try:
            # Update max depth
            stats['max_depth'] = max(stats['max_depth'], depth)
            
            # Process all items in directory
            for item in current_path.iterdir():
                relative_path = item.relative_to(project_path)
                
                if item.is_dir():
                    if item.name not in config.IGNORE_DIRS:
                        stats['total_dirs'] += 1
                        dir_path = str(relative_path)
                        stats['directory_tree'][dir_path] = {
                            'depth': depth,
                            'files': 0,
                            'size': 0
                        }
                        analyze_directory(item, depth + 1)
                else:
                    if item.suffix.lower() in config.SUPPORTED_EXTENSIONS:
                        try:
                            file_size = item.stat().st_size
                            if file_size <= (config.MAX_FILE_SIZE_MB * 1024 * 1024):
                                stats['total_files'] += 1
                                stats['total_size'] += file_size
                                
                                # Update extension stats
                                ext = item.suffix.lower()
                                stats['by_extension'][ext] = stats['by_extension'].get(ext, 0) + 1
                                
                                # Update directory stats
                                dir_path = str(relative_path.parent)
                                if dir_path in stats['directory_tree']:
                                    stats['directory_tree'][dir_path]['files'] += 1
                                    stats['directory_tree'][dir_path]['size'] += file_size
                                
                                stats['by_directory'][dir_path] = stats['by_directory'].get(dir_path, 0) + 1
                        except Exception as e:
                            logger.error(f"Error processing file {relative_path}: {e}")
                            
        except Exception as e:
            logger.error(f"Error analyzing directory {current_path}: {e}")
    
    # Start recursive analysis
    analyze_directory(project_path)
    
    # Add directory depth information to stats
    stats['directory_depth'] = {
        'max_depth': stats['max_depth'],
        'directories_by_depth': {
            depth: len([d for d, info in stats['directory_tree'].items() if info['depth'] == depth])
            for depth in range(stats['max_depth'] + 1)
        }
    }
    
    logger.info("\nAnalysis Summary:")
    logger.info(f"Total Files: {stats['total_files']}")
    logger.info(f"Total Directories: {stats['total_dirs']}")
    logger.info(f"Maximum Directory Depth: {stats['max_depth']}")
    logger.info(f"Total Size: {format_size(stats['total_size'])}")
    logger.info("\nDirectory Structure:")
    for dir_path, info in stats['directory_tree'].items():
        logger.info(f"  {'  ' * info['depth']}{dir_path}/")
        logger.info(f"  {'  ' * (info['depth'] + 1)}Files: {info['files']}")
        logger.info(f"  {'  ' * (info['depth'] + 1)}Size: {format_size(info['size'])}")
    
    files = get_project_files(project_path, config)
    
    return {
        'stats': stats,
        'files': files
    }