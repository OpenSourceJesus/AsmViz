"""
File Finder
Utility functions to find C files, assembly files, and linker scripts in a directory.
"""

import os
from pathlib import Path


def find_source_files(directory):
    """
    Find all C files, assembly files, and linker scripts in a directory recursively.
    
    Args:
        directory: Path to the directory to search
        
    Returns:
        tuple: (c_files, assembly_files, linker_scripts)
            - c_files: List of paths to .c files
            - assembly_files: List of paths to .s and .S files
            - linker_scripts: List of paths to .ld files
    """
    directory = Path(directory).resolve()
    
    if not directory.is_dir():
        # If it's a file, check if it's a valid source file
        if directory.is_file():
            ext = directory.suffix.lower()
            orig_ext = directory.suffix
            if ext == '.c':
                return [str(directory)], [], []
            elif ext == '.s' or orig_ext == '.S':  # .s (lowercase) and .S (uppercase, preprocessed assembly)
                return [], [str(directory)], []
            elif ext == '.ld':
                return [], [], [str(directory)]
            else:
                return [], [], []
    
    c_files = []
    assembly_files = []
    linker_scripts = []
    
    # Walk through directory recursively
    for root, dirs, files in os.walk(directory):
        # Skip hidden directories (starting with .)
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        for file in files:
            file_path = Path(root) / file
            ext = file_path.suffix.lower()
            
            if ext == '.c':
                c_files.append(str(file_path))
            elif ext == '.s' or file_path.suffix == '.S':  # .s (lowercase) and .S (uppercase, preprocessed assembly)
                assembly_files.append(str(file_path))
            elif ext == '.ld':
                linker_scripts.append(str(file_path))
    
    return sorted(c_files), sorted(assembly_files), sorted(linker_scripts)


def is_source_file_or_directory(path):
    """
    Check if a path is a valid source file or directory.
    
    Args:
        path: Path to check
        
    Returns:
        bool: True if path is a valid source file or directory
    """
    path = Path(path)
    
    if path.is_dir():
        return True
    
    if path.is_file():
        ext = path.suffix.lower()
        orig_ext = path.suffix
        return ext == '.c' or ext == '.s' or orig_ext == '.S' or ext == '.ld'
    
    return False
