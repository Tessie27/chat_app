#!/usr/bin/env python3
"""
Cleanup script to remove __pycache__ directories and .pyc files
"""
import os
import shutil
from pathlib import Path

def clean_pycache(start_path="."):
    """Remove all __pycache__ directories and .pyc files"""
    count = 0
    size = 0
    
    print("Cleaning Python cache files...")
    print("-" * 40)
    
    for root, dirs, files in os.walk(start_path):
        # Remove __pycache__ directories
        if "__pycache__" in dirs:
            cache_path = os.path.join(root, "__pycache__")
            try:
                # Calculate size
                dir_size = 0
                for file in os.listdir(cache_path):
                    file_path = os.path.join(cache_path, file)
                    if os.path.isfile(file_path):
                        dir_size += os.path.getsize(file_path)
                
                # Remove directory
                shutil.rmtree(cache_path)
                count += 1
                size += dir_size
                print(f"Removed: {cache_path} ({dir_size:,} bytes)")
            except Exception as e:
                print(f"Error removing {cache_path}: {e}")
        
        # Remove .pyc files (just in case)
        for file in files:
            if file.endswith('.pyc'):
                file_path = os.path.join(root, file)
                try:
                    file_size = os.path.getsize(file_path)
                    os.remove(file_path)
                    count += 1
                    size += file_size
                    print(f"Removed: {file_path} ({file_size:,} bytes)")
                except Exception as e:
                    print(f"Error removing {file_path}: {e}")
    
    print("-" * 40)
    print(f"Cleanup complete!")
    print(f"Removed {count} items")
    print(f"Freed {size:,} bytes ({size/1024:.2f} KB)")

if __name__ == "__main__":
    clean_pycache()