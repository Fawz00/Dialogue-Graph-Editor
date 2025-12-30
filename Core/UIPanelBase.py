from PyQt6.QtWidgets import (QWidget, QVBoxLayout)

from Core.VariableManager import VariableManager

class UIPanelBase(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.var_manager = main_window.var_manager
        self.layout = QVBoxLayout(self)

    def clear(self):
        # Cleanup layout
        while self.layout.count():
            child = self.layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()
    
    def refresh(self):
        # Cleanup layout
        self.clear()

        # Do nothing, to be overridden by subclasses
        pass
