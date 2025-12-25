import os
import shutil

def remove_pycache(directory='.'):
    """Remove all __pycache__ directories recursively."""
    for root, dirs, files in os.walk(directory):
        if '__pycache__' in dirs:
            pycache_path = os.path.join(root, '__pycache__')
            try:
                shutil.rmtree(pycache_path)
                print(f"Removed: {pycache_path}")
            except Exception as e:
                print(f"Error removing {pycache_path}: {e}")

if __name__ == '__main__':
    remove_pycache()
    print("Cleanup complete!")