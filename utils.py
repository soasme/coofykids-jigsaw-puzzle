import os
from pathlib import Path
from proglog import ProgressBarLogger
import streamlit as st

def get_asset_path(dir, path):
    if path.startswith('/'):
        return path
    search_paths = dir.split(',')
    for search_path in search_paths:
        if Path(search_path).joinpath(path).exists():
            return Path(search_path).joinpath(path)
    raise Exception(f'Asset not found: {path}')

class MoviePyProgressLogger(ProgressBarLogger):
    def __init__(self, progress_bar, text='Processing video: '):
        super().__init__()
        self.progress_bar = progress_bar
        self.last_message = ''
        self.text = text

    def callback(self, **changes):
        # Use 'bars' dict to get progress
        bars = self.bars
        if 'frame_index' in bars:
            bar = bars['frame_index']
            index = bar['index']
            total = bar['total']
            if total > 0:
                percentage = int((index / total) * 100)
                self.progress_bar.progress(percentage, text=f"{self.text}: {percentage}%")
