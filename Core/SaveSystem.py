from typing import Any

from Main import MainWindow

class SaveSystem:
    _instance = None

    def __new__(cls, *args: Any, **kwargs: Any):
        if not cls._instance:
            cls._instance = super(SaveSystem, cls).__new__(cls)
        return cls._instance

    def __init__(self, main_window: MainWindow):
        # Initialize your save system here
        self.main_window = main_window
        pass

    def save(self, data: str, filepath: str):
        with open(filepath, 'w') as f:
            f.write(data)

    def load(self, filepath: str):
        with open(filepath, 'r') as f:
            return f.read()