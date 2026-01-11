import sys
from PyQt6.QtWidgets import (QMessageBox, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, 
                             QPushButton, QComboBox, QTreeWidget, QTreeWidgetItem, QMenu)
from PyQt6.QtCore import Qt, pyqtSignal, QObject

from Core.Debug import Debug
from Core.Enums.DataType import DataType
from Core.EventSystem.Event import Event
from Core.EventSystem.EventType import EventType
from Core.Nodes.SetVarNode import SetVarNode
from Core.UIPanelBase import UIPanelBase
from Core.VariableManager import VariableManager
from Core.UIPanel.Utils.TypeDelegate import TypeDelegate

class LogPanel(UIPanelBase):
    def __init__(self, main_window):
        super().__init__(main_window)
        main_window.event_bus.subscribe(EventType.EVENT_LOG_ADDED.value, self.on_log_added)

        self.tree = None
        self.search_edit = None

        self.refresh()

    def clear(self):
        super().clear()

    def refresh(self):
        self.clear()

        # UI Search Section
        form = QHBoxLayout()
        self.search_edit = QLineEdit(placeholderText="Search logs...")
        self.search_edit.textChanged.connect(self.on_search_text_changed)
        form.addWidget(self.search_edit)
        self.layout.addLayout(form)

        # Tree/Table Section
        self.tree = QTreeWidget()
        self.tree.setColumnCount(4)
        self.tree.setHeaderLabels(["Level", "Time", "Message", "Source"])
        self.tree.setAlternatingRowColors(True)
        self.tree.setSelectionBehavior(QTreeWidget.SelectionBehavior.SelectRows)
        self.tree.setUniformRowHeights(False)  # Allow variable row heights for multiline content
        self.tree.setRootIsDecorated(False)
        self.layout.addWidget(self.tree)

        # Add existing logs
        for log_entry in Debug.log_data:
            item = QTreeWidgetItem([
                log_entry["level"],
                log_entry["timestamp"],
                log_entry["message"],
                log_entry["source"]
            ])
            self.tree.addTopLevelItem(item)



    # ========== Event Handlers ==========

    def on_log_added(self, event: Event):
        log_entry = event.payload  # Expecting a dict with keys: timestamp, level, message, source

        item = QTreeWidgetItem([
            log_entry["level"],
            log_entry["timestamp"],
            log_entry["message"],
            log_entry["source"]
        ])

        self.tree.addTopLevelItem(item)

    def on_search_text_changed(self, text):
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            match = False
            for j in range(self.tree.columnCount()):
                if text.lower() in item.text(j).lower():
                    match = True
                    break
            item.setHidden(not match)