from __future__ import annotations
from typing import TYPE_CHECKING

from PyQt6.QtWidgets import QHBoxLayout, QLineEdit

from Core.UIPanelBase import UIPanelBase

if TYPE_CHECKING:
    from Main import MainWindow

class StructVariablePanel(UIPanelBase):
    def __init__(self, main_window: MainWindow):
        super().__init__(main_window)
        self.search_edit = None

        self.refresh()

    def clear(self):
        super().clear()

    def refresh(self):
        self.clear()

        # UI Search Section
        form = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search Struct Variables...")
        self.search_edit.textChanged.connect(self.on_search_text_changed) # type: ignore
        form.addWidget(self.search_edit)
        self.v_layout.addLayout(form)



    # ========== Event Handlers ==========

    def on_search_text_changed(self, text: str):
        # TODO: Implement search/filtering logic for structures
        return