import os
import shutil

def clean_pycache(directory):
    for root, dirs, _ in os.walk(directory):
        for dir_name in dirs:
            if dir_name == '__pycache__':
                dir_path = os.path.join(root, dir_name)
                print(f"Removing {dir_path}")
                shutil.rmtree(dir_path, ignore_errors=True)
        
        # Remove .pyc and .pyo files
        for file in os.listdir(root):
            if file.endswith(('.pyc', '.pyo')):
                file_path = os.path.join(root, file)
                print(f"Removing {file_path}")
                try:
                    os.unlink(file_path)
                except Exception as e:
                    print(f"Error removing {file_path}: {e}")

if __name__ == "__main__":
    clean_pycache(os.getcwd())
    print("Cache cleaned successfully!")
