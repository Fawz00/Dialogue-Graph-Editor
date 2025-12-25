import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QGraphicsScene, QGraphicsView, 
                             QGraphicsItem, QGraphicsPathItem, QGraphicsProxyWidget,
                             QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QComboBox, QDockWidget, QListWidget, QFormLayout,
                             QMenu, QTreeWidget, QTreeWidgetItem, QMessageBox)
from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QPainterPath, QFont, QAction, QKeySequence

from Style import STYLES

from Core.VariableManager import VariableManager
from Core.BaseNode import BaseNode

from Core.Graph.SocketItem import SocketItem
from Core.Graph.EdgeItem import EdgeItem

from Core.Nodes.StartNode import StartNode
from Core.Nodes.DialogueNode import DialogueNode
from Core.Nodes.SetVarNode import SetVarNode

from Core.View.GraphScene import GraphScene
from Core.View.GraphView import GraphView

from Core.UIPanel.PropertiesPanel import PropertiesPanel
from Core.UIPanel.GlobalVariablePanel import GlobalVariablePanel

# ==========================================
# 6. MAIN WINDOW
# ==========================================

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Python Dialogue Graph Editor")
        self.resize(1000, 700)
        self.setStyleSheet("QMainWindow { background-color: #222; color: #EEE; }")

        # Data logic
        self.var_manager = VariableManager()

        # Connect signal untuk update node jika variabel diubah
        self.var_manager.variable_updated.connect(self.on_variable_updated)
        self.var_manager.variable_created.connect(self.on_variable_created)
        self.var_manager.variable_deleted.connect(self.on_variable_deleted)

        # Center Canvas
        self.scene = GraphScene()
        self.view = GraphView(self.scene, self)
        self.setCentralWidget(self.view)

        # Panels
        self.setup_docks()

        # 2. Setup Menu Bar
        self.setup_menu()

        # Tambahkan Start Node DI AKHIR inisialisasi
        self.create_initial_nodes()

    def setup_docks(self):
        # Kita simpan dock ke dalam 'self' agar bisa diakses oleh Menu
        
        # --- Variables Dock (Left) ---
        self.dock_vars = QDockWidget("Global Variables", self)
        self.dock_vars.setObjectName("VariablesDock") # ID unik untuk save/restore state layout
        self.dock_vars.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        
        self.var_panel = GlobalVariablePanel(self.var_manager)
        self.dock_vars.setWidget(self.var_panel)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.dock_vars)

        # --- Properties Dock (Right) ---
        self.dock_props = QDockWidget("Details", self)
        self.dock_props.setObjectName("PropertiesDock")
        self.dock_props.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        
        self.properties_panel = PropertiesPanel()
        self.dock_props.setWidget(self.properties_panel)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dock_props)
    
    def setup_menu(self):
        menu_bar = self.menuBar()
        
        # === FILE MENU ===
        file_menu = menu_bar.addMenu("&File") # Tanda & membuat shortcut Alt+F
        
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
        
        # === VIEW MENU ===
        view_menu = menu_bar.addMenu("&View")
        
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
        window_menu.addAction(self.dock_props.toggleViewAction())

        # === HELP MENU ===
        help_menu = menu_bar.addMenu("&Help")
        
        act_about = QAction("About", self)
        act_about.triggered.connect(self.help_about)
        help_menu.addAction(act_about)
    
    def create_initial_nodes(self):
        self.start_node = StartNode()
        self.start_node.setPos(2500, 2500) # Koordinat awal
        self.scene.addItem(self.start_node)
        
        # Fokuskan kamera ke arah start node
        self.view.centerOn(self.start_node)
    
    # --- ACTION HANDLERS ---

    def view_reset_layout(self):
        # 1. Pastikan dock terlihat (mungkin user me-close nya)
        self.dock_vars.setVisible(True)
        self.dock_props.setVisible(True)
        
        # 2. Kembalikan ke posisi awal (Floating false, area specific)
        self.dock_vars.setFloating(False)
        self.dock_props.setFloating(False)
        
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.dock_vars)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dock_props)
        
        # Opsional: Reset ukuran window utama jika mau
        # self.resize(1000, 700)

    def file_open(self):
        print("Menu: Open clicked") # Placeholder

    def file_save(self):
        print("Menu: Save clicked") # Placeholder

    def file_save_as(self):
        print("Menu: Save As clicked") # Placeholder

    def file_export(self):
        print("Menu: Export clicked") # Placeholder
        
    def help_about(self):
        QMessageBox.about(self, "About Dialogue Editor", 
                          "Python Dialogue Graph Editor v0.1\n\n"
                          "Inspired by Unreal Engine Blueprints.\n"
                          "Created with PyQt6.")

    # Handler ketika variabel global diubah
    def on_variable_updated(self, old_name, new_name):
        """Dipanggil saat variabel diubah"""
        
        # 1. Update logika node dan putus koneksi yang tidak valid (kode sebelumnya)
        for item in self.scene.items():
            if isinstance(item, SetVarNode):
                if item.selected_var == old_name:
                    item.selected_var = new_name
                    item.set_property("Variable", new_name)
                self.validate_node_connections(item)

        # 2. REFRESH PANEL DETAILS
        # Jika node yang sedang diedit di panel details terpengaruh, refresh UI-nya
        self.properties_panel.refresh()
    
    def on_variable_deleted(self, name):
        """Dipanggil saat variabel dihapus"""
        for item in self.scene.items():
            if isinstance(item, SetVarNode):
                if item.selected_var == name:
                    item.selected_var = ""
                    item.set_property("Variable", "")

                    # Putus semua koneksi pada socket data sebelum dihapus
                    if item.in_data:
                        self.view.clear_socket_connections(item.in_data)
                    if item.out_data:
                        self.view.clear_socket_connections(item.out_data)
                    
                    # Bersihkan socket secara permanen
                    item.update_sockets_by_variable("")
        
        # 2. REFRESH PANEL DETAILS
        self.properties_panel.refresh()
    
    def on_variable_created(self, name):
        """Dipanggil saat variabel dibuat"""
        # Hanya perlu refresh panel details
        self.properties_panel.refresh()
    
    def validate_node_connections(self, node):
        """Memutus kabel jika tipe data socket berubah dan tidak cocok dengan kabelnya"""
        for socket in node.inputs + node.outputs:
            if socket.socket_type == "exec": continue # Lewati alur eksekusi
            
            for edge in socket.edges[:]:
                # Ambil socket lawan
                other_socket = edge.start_socket if edge.end_socket == socket else edge.end_socket
                
                # Jika tipe data sudah tidak sama, putus koneksinya!
                if socket.socket_type != other_socket.socket_type:
                    print(f"Disconnecting incompatible link: {socket.socket_type} vs {other_socket.socket_type}")
                    self.view.clear_socket_connections(socket)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())