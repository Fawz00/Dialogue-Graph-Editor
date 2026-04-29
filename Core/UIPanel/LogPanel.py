import os
import subprocess
import sys
import urllib.parse
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QMessageBox, QTextBrowser, QToolButton, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, 
                             QPushButton, QComboBox, QTreeWidget, QTreeWidgetItem, QMenu, QTextEdit,
                             QHeaderView, QSplitter)
from PyQt6.QtGui import QAction, QColor, QBrush, QFont

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
        self.detail_panel = None

        self.refresh()

    def clear(self):
        super().clear()

    def refresh(self):
        self.clear()

        # Search bar
        form = QHBoxLayout()

        # SEARCH
        self.search_edit = QLineEdit(placeholderText="Search logs...")
        self.search_edit.textChanged.connect(self.apply_filters)
        form.addWidget(self.search_edit)

        # LEVEL FILTER
        self.filter_btn = QToolButton()
        self.filter_btn.setText("FILTER")
        self.filter_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.filter_btn.setMinimumWidth(90)
        self.filter_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        form.addWidget(self.filter_btn)

        self.filter_menu = QMenu(self)

        self.level_actions = {}

        levels = ["INFO", "DEBUG", "WARNING", "ERROR", "CRITICAL"]

        for level in levels:
            action = QAction(level, self)
            action.setCheckable(True)
            action.setChecked(True)
            action.triggered.connect(self.apply_filters)

            self.filter_menu.addAction(action)
            self.level_actions[level] = action

        self.filter_btn.setMenu(self.filter_menu)

        # AUTO SCROLL TOGGLE
        self.auto_scroll_btn = QPushButton("Auto Scroll")
        self.auto_scroll_btn.setCheckable(True)
        self.auto_scroll_btn.setChecked(True)
        form.addWidget(self.auto_scroll_btn)

        # CLEAR BUTTON
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self.clear_logs)
        form.addWidget(self.clear_btn)

        self.layout.addLayout(form)

        # === MAIN CONTENT ===
        self.splitter = QSplitter(Qt.Orientation.Horizontal)

        # LEFT: TREE
        self.tree = QTreeWidget()
        self.tree.setColumnCount(4)
        self.tree.setHeaderLabels(["Level", "Time", "Message", "Source"])
        self.tree.setHorizontalScrollMode(QTreeWidget.ScrollMode.ScrollPerPixel)
        self.tree.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.tree.itemClicked.connect(self.on_item_clicked)

        self.splitter.addWidget(self.tree)

        # RIGHT: DETAIL
        self.detail_panel = QTextBrowser()
        self.detail_panel.setReadOnly(True)
        self.detail_panel.setOpenExternalLinks(False)
        self.detail_panel.setOpenLinks(False)
        self.detail_panel.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextBrowserInteraction
        )
        self.detail_panel.anchorClicked.connect(self.on_traceback_clicked)

        self.splitter.addWidget(self.detail_panel)

        # default ratio (kiri lebih besar)
        self.splitter.setSizes([700, 300])

        self.layout.addWidget(self.splitter)

        # Load logs
        for log_entry in Debug.log_data:
            self.add_log_item(log_entry)



    # ========== Event Handlers ==========
    
    def on_log_added(self, event: Event):
        self.add_log_item(event.payload)

        self.apply_filters()

        if self.auto_scroll_btn.isChecked():
            self.tree.scrollToBottom()

    def apply_filters(self):
        text = self.search_edit.text().lower()
        selected_levels = self.get_selected_levels()

        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)

            # ambil data asli
            log_entry = item.data(0, Qt.ItemDataRole.UserRole)
            level = log_entry.get("level", "").upper()

            # === FILTER LEVEL ===
            level_match = (len(selected_levels) == 0 or level in selected_levels)

            # === FILTER TEXT ===
            text_match = False
            if text == "":
                text_match = True
            else:
                for j in range(self.tree.columnCount()):
                    if text in item.text(j).lower():
                        text_match = True
                        break

            item.setHidden(not (level_match and text_match))



    # ========== Qt Events ==========

    def resizeEvent(self, event):
        super().resizeEvent(event)

        width = self.width()
        height = self.height()

        # kalau tinggi lebih besar → stack vertical
        if height > width:
            self.splitter.setOrientation(Qt.Orientation.Vertical)
        else:
            self.splitter.setOrientation(Qt.Orientation.Horizontal)
    


    # ========== Helper Methods ==========

    def apply_log_color(self, item, level):
        color_map = {
            "INFO": QColor("#00bcd4"),
            "DEBUG": QColor("#9e9e9e"),
            "WARNING": QColor("#ff9800"),
            "ERROR": QColor("#f44336"),
            "CRITICAL": QColor("#d32f2f"),
        }

        color = color_map.get(level.upper())
        if color:
            for col in range(item.columnCount()):
                item.setForeground(col, QBrush(color))
    
    def add_log_item(self, log_entry):
        item = QTreeWidgetItem([
            log_entry["level"],
            log_entry["timestamp"],
            log_entry["message"],
            log_entry["source"]
        ])

        # simpan full data (termasuk traceback)
        item.setData(0, Qt.ItemDataRole.UserRole, log_entry)

        self.apply_log_color(item, log_entry["level"])

        self.tree.addTopLevelItem(item)
    
    def on_item_clicked(self, item, column):
        log_entry = item.data(0, Qt.ItemDataRole.UserRole)

        if not log_entry:
            return

        self.detail_panel.setHtml(self.format_log_detail(log_entry))
    
    def format_log_detail(self, log_entry):
        level = log_entry.get("level", "").upper()
        timestamp = log_entry.get("timestamp", "")
        source = log_entry.get("source", "")
        message = log_entry.get("message", "")
        traceback = log_entry.get("traceback", "No traceback available")

        formatted = []

        for frame in log_entry.get("traceback", []):
            file_path = frame.filename
            line_no = frame.lineno

            formatted.append(
                f'<a href="{file_path}|{line_no}" style="color:#80cbc4; text-decoration:none;">'
                f'{file_path}:{line_no} in {frame.function}'
                f'</a>'
            )
            
            if frame.code_context:
                formatted.append(f"  {frame.code_context[0].strip()}")

        traceback_str = "\n".join(formatted)

        # warna level
        level_color = {
            "INFO": "#4fc3f7",
            "DEBUG": "#9e9e9e",
            "WARNING": "#ffb74d",
            "ERROR": "#ef5350",
            "CRITICAL": "#e53935"
        }.get(level, "#ffffff")

        html = f"""
        <div style="font-family: Consolas, monospace; font-size: 12px;">

            <!-- HEADER -->
            <div style="margin-bottom: 8px;">
                <span style="color:{level_color}; font-weight:bold;">
                    ● {level}
                </span>
                <span style="color:#888;"> | {timestamp}</span>
            </div>

            <!-- SOURCE -->
            <div style="margin-bottom: 10px;">
                <b style="color:#ccc;">Source:</b><br>
                <span style="color:#aaa;">{source}</span>
            </div>

            <!-- MESSAGE -->
            <div style="margin-bottom: 10px;">
                <b style="color:#ccc;">Message:</b>
                <pre style="
                    background:#1e1e1e;
                    padding:8px;
                    border-radius:4px;
                    color:#e0e0e0;
                ">{message}</pre>
            </div>

            <!-- TRACEBACK -->
            <div>
                <b style="color:#ccc;">Traceback:</b>
                <pre style="
                    background:#2a1a1a;
                    padding:8px;
                    border-radius:4px;
                    color:#eaea80;
                ">{traceback_str}</pre>
            </div>

        </div>
        """

        return html

    def clear_logs(self):
        self.tree.clear()
        self.detail_panel.clear()
    
    def get_selected_levels(self):
        selected = []

        for level, action in self.level_actions.items():
            if action.isChecked():
                selected.append(level)

        return selected

    def on_traceback_clicked(self, url):
        data = url.toString()

        # Decode percent-encoded URL components
        data = urllib.parse.unquote(data)

        if "|" in data:
            file_path, line = data.split("|", 1)
        else:
            file_path = data
            line = None

        if not os.path.exists(file_path):
            return

        try:
            target = f"{file_path}:{line}" if line else file_path
            if sys.platform == "win32":
                subprocess.Popen(["code", "-g", target])
            elif sys.platform == "darwin":
                subprocess.Popen(["open", target])
            else:
                subprocess.Popen(["xdg-open", target])
        except Exception:
            try:
                os.startfile(file_path)
            except Exception:
                pass