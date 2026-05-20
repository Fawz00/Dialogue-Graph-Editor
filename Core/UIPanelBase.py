from __future__ import annotations
from typing import TYPE_CHECKING

from PyQt6.QtWidgets import (QWidget, QVBoxLayout)

from Core.VariableManager import VariableManager

if TYPE_CHECKING:
    from Main import MainWindow

class UIPanelBase(QWidget):
    def __init__(self, main_window: MainWindow):
        super().__init__()
        self.main_window = main_window
        self.var_manager: VariableManager = main_window.var_manager
        # avoid shadowing QWidget.layout() method (QWidget.layout is a method in PyQt)
        # use a different attribute name for the layout to satisfy static type checkers
        self.v_layout: QVBoxLayout = QVBoxLayout(self)

    def clear(self):
        # Cleanup layout
        while self.v_layout.count():
            child = self.v_layout.takeAt(0)
            if child is not None and child.widget():
                widget = child.widget()
                if widget is not None:
                    widget.deleteLater()
    
    def refresh(self):
        # Cleanup layout
        self.clear()

        # Do nothing, to be overridden by subclasses
        pass
