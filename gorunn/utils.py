import shutil

def copy_directory(source, destination):
    """Copy entire directory from source to destination."""
    shutil.copytree(source, destination)

def remove_directory(directory_path):
    """Remove the directory if it exists."""
    if directory_path.exists():
        shutil.rmtree(directory_path)
