import os
from pathlib import Path

def get_asset_path(dir, path):
    if path.startswith('/'):
        return path
    search_paths = dir.split(',')
    for search_path in search_paths:
        if Path(search_path).joinpath(path).exists():
            return Path(search_path).joinpath(path)
    raise Exception(f'Asset not found: {path}')
