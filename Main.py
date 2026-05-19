import sys, select, threading 
from PyQt6.QtWidgets import (QApplication, QMainWindow, QGraphicsScene, QGraphicsView, 
                             QGraphicsItem, QGraphicsPathItem, QGraphicsProxyWidget,
                             QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QLayout,
                             QPushButton, QComboBox, QDockWidget, QListWidget, QFormLayout,
                             QMenu, QTreeWidget, QTreeWidgetItem, QMessageBox, QToolBar, QMenuBar, QStatusBar,
                             QSizePolicy)
from PyQt6.QtCore import Qt, QPointF, QRectF, QSize
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QPainterPath, QFont, QAction, QKeySequence, QIcon, QUndoStack

from Core.Debug import Debug
from Core.EventSystem.Event import Event
from Core.EventSystem.EventBus import EventBus
from Core.EventSystem.EventType import EventType

from Core.Execution.NodeRunner import NodeRunner
from Core.UIPanel.FunctionsPanel import FunctionsPanel
from Core.UIPanel.LogPanel import LogPanel
from Core.UIPanel.StructVariablePanel import StructVariablePanel
from Core.VariableManager import VariableManager
from Core.Graph.BaseNode import BaseNode

from Core.Graph.SocketItem import SocketItem
from Core.Graph.EdgeItem import EdgeItem

from Core.Nodes.StartNode import StartNode
from Core.Nodes.DialogueNode import DialogueNode
from Core.Nodes.SetVarNode import SetVarNode

from Core.View.GraphScene import GraphScene
from Core.View.GraphView import GraphView

from Core.UIPanel.PropertiesPanel import PropertiesPanel
from Core.UIPanel.GlobalVariablePanel import GlobalVariablePanel

from Style import STYLES

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(1000, 700)
        self.setStyleSheet("QMainWindow { background-color: #222; color: #EEE; }")

        # Undo Stack
        self.undo_stack = QUndoStack(self)

        # Editor EventBus
        self.event_bus = EventBus()

        # Data logic
        self.var_manager = VariableManager(self)

        # Setup logger
        Debug.set_main_window(self)

        # Connect signal untuk update node jika variabel diubah
        self.event_bus.subscribe(EventType.EVENT_VARIABLE_UPDATED.value, self.on_variable_updated)
        self.event_bus.subscribe(EventType.EVENT_VARIABLE_REMOVED.value, self.on_variable_deleted)

        self.event_bus.subscribe(EventType.EVENT_EXECUTION_STARTED.value, self.on_execution_start)
        self.event_bus.subscribe(EventType.EVENT_EXECUTION_PAUSED.value, self.on_execution_pause)
        self.event_bus.subscribe(EventType.EVENT_EXECUTION_RESUMED.value, self.on_execution_resume)
        self.event_bus.subscribe(EventType.EVENT_EXECUTION_STOPPED.value, self.on_execution_stop)

        # Executor
        self.node_runner = NodeRunner(self)

        # Center Canvas
        self.scene = GraphScene()
        self.view = GraphView(self.scene, self)
        self.setCentralWidget(self.view)

        # Setup Toolbar
        self.setup_toolbar()

        # Panels
        self.setup_docks()

        # Setup Menu Bar
        self.setup_menu()

        # Tambahkan Start Node DI AKHIR inisialisasi
        BaseNode.main_window = self
        self.create_initial_nodes()

    def setup_docks(self):
        # Kita simpan dock ke dalam 'self' agar bisa diakses oleh Menu
        
        # --- Variables Dock (Left) ---
        self.dock_vars = QDockWidget("Global Variables", self)
        self.dock_vars.setObjectName("VariablesDock") # ID unik untuk save/restore state layout
        self.dock_vars.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea | Qt.DockWidgetArea.BottomDockWidgetArea)
        
        self.var_panel = GlobalVariablePanel(self)
        self.dock_vars.setWidget(self.var_panel)

        # --- Structures Dock (Left) ---
        self.dock_structs = QDockWidget("Structures", self)
        self.dock_structs.setObjectName("StructuresDock")
        self.dock_structs.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea | Qt.DockWidgetArea.BottomDockWidgetArea)

        self.struct_panel = StructVariablePanel(self)
        self.dock_structs.setWidget(self.struct_panel)

        # --- Functions Dock (Left) ---
        self.dock_funcs = QDockWidget("Functions", self)
        self.dock_funcs.setObjectName("FunctionsDock")
        self.dock_funcs.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea | Qt.DockWidgetArea.BottomDockWidgetArea)

        self.func_panel = FunctionsPanel(self)
        self.dock_funcs.setWidget(self.func_panel)

        # --- Properties Dock (Right) ---
        self.dock_props = QDockWidget("Inspector", self)
        self.dock_props.setObjectName("PropertiesDock")
        self.dock_props.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea | Qt.DockWidgetArea.BottomDockWidgetArea)
        
        self.properties_panel = PropertiesPanel(self)
        self.dock_props.setWidget(self.properties_panel)

        # --- Log Dock (Bottom) ---
        self.log_dock = QDockWidget("Log", self)
        self.log_dock.setObjectName("LogDock")
        
        self.log_panel = LogPanel(self)
        self.log_dock.setWidget(self.log_panel)

        # --- Set View ---
        self.view_reset_layout(None) # Atur posisi dan visibilitas dock sesuai layout awal

        # --- Register event ---
        self.var_panel.variable_selected.connect(self.properties_panel.load_variable)        
    
    def setup_toolbar(self):
        self.toolbar = QToolBar("Execution Control")
        self.toolbar.setIconSize(QSize(18, 18))
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolbar)
        self.toolbar.setMovable(False)

        # Left Spacer
        left_spacer = QWidget()
        left_spacer.setSizePolicy(
            QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        )
        self.toolbar.addWidget(left_spacer)

        # Action Run
        self.run_act = QAction(QIcon("resources/run.png"), "Run", self)
        self.run_act.triggered.connect(self.on_run_pressed)
        self.toolbar.addAction(self.run_act)

        # Action Pause
        self.pause_act = QAction(QIcon("resources/pause.png"), "Pause", self)
        self.pause_act.setEnabled(False) # Mati sampai dijalankan
        self.pause_act.triggered.connect(self.on_pause_pressed)
        self.toolbar.addAction(self.pause_act)

        # Action Stop
        self.stop_act = QAction(QIcon("resources/stop.png"), "Stop", self)
        self.stop_act.setEnabled(False)
        self.stop_act.triggered.connect(self.on_stop_pressed)
        self.toolbar.addAction(self.stop_act)

        # Right Spacer
        right_spacer = QWidget()
        right_spacer.setSizePolicy(
            QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        )
        self.toolbar.addWidget(right_spacer)

    def setup_menu(self):
        self.menu_bar = self.menuBar()
        
        # === FILE MENU ===
        file_menu = self.menu_bar.addMenu("&File") # Tanda & membuat shortcut Alt+F
        
        # Actions (Placeholder)
        act_open = QAction("Open", self)
        act_open.setShortcut(QKeySequence.StandardKey.Open)
        act_open.triggered.connect(self.file_open)
        file_menu.addAction(act_open)

        act_save = QAction("Save", self)
        act_save.setShortcut(QKeySequence.StandardKey.Save)
        act_save.triggered.connect(self.file_save)
        file_menu.addAction(act_save)

        act_save_as = QAction("Save As...", self)
        act_save_as.setShortcut(QKeySequence.StandardKey.SaveAs)
        act_save_as.triggered.connect(self.file_save_as)
        file_menu.addAction(act_save_as)
        
        file_menu.addSeparator() # Garis pemisah
        
        act_export = QAction("Export", self)
        act_export.triggered.connect(self.file_export)
        file_menu.addAction(act_export)

        # === EDIT MENU ===
        edit_menu = self.menu_bar.addMenu("&Edit")

        # Actions
        # act_undo = QAction("Undo", self)
        act_undo = self.undo_stack.createUndoAction(self, "Undo")
        act_undo.setShortcut(QKeySequence.StandardKey.Undo)
        edit_menu.addAction(act_undo)

        # act_redo = QAction("Redo", self)
        act_redo = self.undo_stack.createRedoAction(self, "Redo")
        act_redo.setShortcut(QKeySequence.StandardKey.Redo)
        edit_menu.addAction(act_redo)

        edit_menu.addSeparator()

        act_preferences = QAction("Preferences", self)
        edit_menu.addAction(act_preferences)

        act_project_settings = QAction("Project Settings", self)
        edit_menu.addAction(act_project_settings)
        
        # === VIEW MENU ===
        view_menu = self.menu_bar.addMenu("&View")
        
        # Reset Layout Action
        act_reset = QAction("Reset Layout", self)
        act_reset.triggered.connect(self.view_reset_layout)
        view_menu.addAction(act_reset)
        
        view_menu.addSeparator()

        # Window Submenu
        window_menu = view_menu.addMenu("Window")
        
        # Magic PyQt: toggleViewAction()
        # Method ini otomatis membuat Action yang 'Checkable'.
        # Jika dock tertutup, menu ini jadi unchecked. Jika diklik, dock terbuka kembali.
        window_menu.addAction(self.dock_vars.toggleViewAction())
        window_menu.addAction(self.dock_structs.toggleViewAction())
        window_menu.addAction(self.dock_funcs.toggleViewAction())
        window_menu.addAction(self.dock_props.toggleViewAction())
        window_menu.addAction(self.log_dock.toggleViewAction())
        window_menu.addAction(self.toolbar.toggleViewAction())

        # === HELP MENU ===
        help_menu = self.menu_bar.addMenu("&Help")
        
        act_about = QAction("About", self)
        act_about.triggered.connect(self.help_about)
        help_menu.addAction(act_about)

        # === WINDOW MENU ===
        app_menu = self.menu_bar.addMenu("&Application")
        
        act_quit = QAction("Quit", self)
        act_quit.triggered.connect(self.quit_application)
        app_menu.addAction(act_quit)
    
    def create_initial_nodes(self):
        self.start_node = StartNode()
        self.start_node.setPos(2500, 2500) # Koordinat awal
        self.scene.addItem(self.start_node)
        
        # Fokuskan kamera ke arah start node
        self.view.centerOn(self.start_node)



    # ===== ACTION HANDLERS =====
    #region Action Handlers

    def view_reset_layout(self, menu: QMenuBar):
        # 1. Pastikan dock terlihat (mungkin user me-close nya)
        self.dock_vars.setVisible(True)
        self.dock_structs.setVisible(True)
        self.dock_funcs.setVisible(True)
        self.dock_props.setVisible(True)
        self.log_dock.setVisible(True)
        self.toolbar.setVisible(True)
        
        # 2. Kembalikan ke posisi awal (Floating false, area specific)
        self.dock_vars.setFloating(False)
        self.dock_structs.setFloating(False)
        self.dock_funcs.setFloating(False)
        self.dock_props.setFloating(False)
        self.log_dock.setFloating(False)
        
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.dock_vars)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.dock_structs)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.dock_funcs)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dock_props)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.log_dock)

        self.tabifyDockWidget(self.dock_structs, self.dock_funcs)
        
        self.toolbar.toggleViewAction().setChecked(True)
        
        # Opsional: Reset ukuran window utama jika mau
        # self.resize(1000, 700)
    
    def on_run_pressed(self):
        # Panggil fungsi interpreter
        if self.node_runner.is_running and self.node_runner.is_paused:
            self.node_runner.request_resume()
        else:
            self.node_runner.start_execution(self.start_node)
    
    def on_pause_pressed(self):
        # Panggil fungsi pause pada interpreter
        self.node_runner.request_pause()

    def on_stop_pressed(self):
        # Panggil fungsi stop pada interpreter
        self.node_runner.request_stop()

    def file_open(self):
        print("Menu: Open clicked") # Placeholder

    def file_save(self):
        print("Menu: Save clicked") # Placeholder

    def file_save_as(self):
        print("Menu: Save As clicked") # Placeholder

    def file_export(self):
        print("Menu: Export clicked") # Placeholder

    def help_about(self):
        QMessageBox.about(self, f"About Visual Graph Editor", 
                          f"Python Visual Graph Editor v{'.'.join(map(str, APP_VERSION))}\n\n"
                          "Inspired by Unreal Engine Blueprints.\n"
                          "Created with PyQt6.")
    
    def quit_application(self):
        reply = QMessageBox.question(
            self,
            "Confirm Quit",
            "Are you sure you want to quit?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            QApplication.quit()

    def closeEvent(self, event):
        if self.quit_application():
            event.accept()
        else:
            event.ignore()

    #endregion Action Handlers



    # ===== Handler ketika variabel global diubah =====
    #region Variable Change Handlers

    def on_variable_updated(self, event: Event):
        """Dipanggil saat variabel diubah"""
        old_name = event.payload.get("old_name")
        new_name = event.payload.get("new_name")
        
        # 1. Update logika node dan putus koneksi yang tidak valid (kode sebelumnya)
        for item in self.scene.items():
            if isinstance(item, SetVarNode):
                if item.selected_var == old_name:
                    item.selected_var = new_name
                    item.set_property("Variable", new_name)
                    item.update_sockets_by_variable(new_name)
                item.validate_socket_connections()

        # 2. REFRESH PANEL DETAILS
        # Jika node yang sedang diedit di panel details terpengaruh, refresh UI-nya
        self.var_panel.refresh()
        self.properties_panel.refresh()
    
    def on_variable_deleted(self, event: Event):
        """Dipanggil saat variabel dihapus"""
        name = event.payload.get("name")

        for item in self.scene.items():
            if isinstance(item, SetVarNode):
                if item.selected_var == name:
                    item.selected_var = ""
                    item.set_property(["Variable"], "")

                    # Putus semua koneksi pada socket data sebelum dihapus
                    if item.in_data:
                        item.remove_socket(item.in_data)
                    if item.out_data:
                        item.remove_socket(item.out_data)
                    
                    # Bersihkan socket secara permanen
                    item.update_sockets_by_variable("")
        
        # 2. REFRESH PANEL DETAILS
        self.var_panel.refresh()
        self.properties_panel.refresh()
    
    #endregion Variable Change Handlers

    # ===== Handler execution flow =====
    #region Execution Flow

    def on_execution_start(self, event: Event):
        self.run_act.setEnabled(False)
        self.pause_act.setEnabled(True)
        self.stop_act.setEnabled(True)
    
    def on_execution_pause(self, event: Event):
        self.run_act.setEnabled(True)
        self.pause_act.setEnabled(False)
        self.stop_act.setEnabled(True)

    def on_execution_resume(self, event: Event):
        self.run_act.setEnabled(False)
        self.pause_act.setEnabled(True)
        self.stop_act.setEnabled(True)

    def on_execution_stop(self, event: Event):
        self.run_act.setEnabled(True)
        self.pause_act.setEnabled(False)
        self.stop_act.setEnabled(False)

    #endregion Execution Flow



# ===== Entry Point =====

APP_VERSION = [0, 0, 1]
APP_NAME = "Visual Graph Editor"

if __name__ == '__main__':
    # QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseSoftwareOpenGL, True)
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_DontUseNativeMenuBar, True)
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_DontUseNativeDialogs, True)

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(".".join(map(str, APP_VERSION)))
    app.setOrganizationName("FawwazHP")

    window = MainWindow()
    # window.setGeometry(50, 50, 1020, 720)
    window.show()
    sys.exit(app.exec())