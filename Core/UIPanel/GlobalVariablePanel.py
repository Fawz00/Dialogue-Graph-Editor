import sys
from PyQt6.QtWidgets import (QMessageBox, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, 
                             QPushButton, QComboBox, QTreeWidget, QTreeWidgetItem, QMenu)
from PyQt6.QtCore import Qt, pyqtSignal

from Core.Debug.Debug import Debug
from Core.Enums.DataType import DataType
from Core.EventSystem.Event import Event
from Core.EventSystem.EventType import EventType
from Core.Nodes.SetVarNode import SetVarNode
from Core.UIPanelBase import UIPanelBase
from Core.VariableManager import VariableManager
from Core.UIPanel.Utils.TypeDelegate import TypeDelegate
from Core.Structures.Variable import Variable

class GlobalVariablePanel(UIPanelBase):
    # Signal untuk mengirim data variabel yang dipilih ke MainWindow
    variable_selected = pyqtSignal(str, Variable)
    
    def __init__(self, main_window):
        super().__init__(main_window)
        self.refresh()

        main_window.event_bus.subscribe(EventType.EVENT_VARIABLE_UPDATED.value, self._on_variable_updated)
        main_window.event_bus.subscribe(EventType.EVENT_VARIABLE_ADDED.value, self._on_variable_created)
        main_window.event_bus.subscribe(EventType.EVENT_VARIABLE_REMOVED.value, self._on_variable_deleted)
    
    # ========== Event Handlers ==========
    def _on_variable_created(self, event: Event):
        self.refresh()
    def _on_variable_deleted(self, event: Event):
        self.refresh()
    def _on_variable_updated(self, event: Event):
        self.refresh()
    
    # ========== UI Methods ==========

    def clear(self):
        # 1. Putuskan sinyal tree lama (kalau ada)
        if hasattr(self, "tree") and self.tree:
            try:
                self.tree.itemClicked.disconnect()
                self.tree.itemChanged.disconnect()
                self.tree.customContextMenuRequested.disconnect()
            except TypeError:
                pass  # kalau belum terhubung, abaikan

        # 2. Hapus semua item dari layout utama
        while self.layout.count():
            item = self.layout.takeAt(0)

            widget = item.widget()
            layout = item.layout()

            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()

            elif layout is not None:
                self._clear_layout(layout)

        # 3. Reset referensi penting
        self.tree = None
        self.name_edit = None
        self.type_combo = None
    
    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)

            widget = item.widget()
            child_layout = item.layout()

            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()

            elif child_layout is not None:
                self._clear_layout(child_layout)
    
    def refresh(self):
        self.clear()

        # UI Create Section
        form = QHBoxLayout()
        self.name_edit = QLineEdit(placeholderText="Variable Name")
        self.type_combo = QComboBox()
        self.type_combo.addItems(VariableManager.SUPPORTED_TYPES_AS_STRING)
        btn_add = QPushButton("+ Add")
        btn_add.clicked.connect(self.add_variable)
        form.addWidget(self.name_edit); form.addWidget(self.type_combo); form.addWidget(btn_add)
        self.layout.addLayout(form)
        
        # Tree/Table Section
        self.tree = QTreeWidget()
        self.tree.setColumnCount(2)
        self.tree.setHeaderLabels(["Name", "Type"])
        
        # PASANG DROPDOWN KE KOLOM TYPE (Index 1)
        self.tree.setItemDelegateForColumn(1, TypeDelegate(self))

        self.tree.itemClicked.connect(self.on_item_clicked)

        # Aktifkan Context Menu
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)
        
        # Hubungkan event key press
        self.tree.keyPressEvent = self.handle_key_press
        
        self.tree.itemChanged.connect(self.on_item_changed)
        self.layout.addWidget(self.tree)

        for var_name, var_data in self.var_manager.get_all_global_variables().items():
            v_type = self.type_combo.currentText()
            v_type = DataType(var_data.type).value if var_data.type else "Unknown"
            item = QTreeWidgetItem([var_name, v_type])
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
            self.tree.addTopLevelItem(item)
    
    def on_item_clicked(self, item, column):
        var_name = item.text(0)
        var_data = self.var_manager.get_global_variable(var_name)
        if var_data:
            self.variable_selected.emit(var_name, var_data)

    def add_variable(self):
        name = self.name_edit.text().strip()
        if not name: return
        
        # Validasi: Cek apakah nama sudah ada
        if self.var_manager.get_global_variable(name) is not None:
            QMessageBox.warning(self, "Duplicate Name", f"Variable with name '{name}' already exists!")
            self.name_edit.setStyleSheet("background-color: #ffcccc;") # Feedback merah
            return

        self.name_edit.setStyleSheet("") # Reset style jika berhasil
        v_type = self.type_combo.currentText()
        default_val = VariableManager.get_default_value(DataType(v_type))
        
        self.var_manager.create_global_variable(name, v_type, default_val)
    
    def delete_variable_item(self, item):
        """Fungsi helper untuk menghapus variabel secara bersih"""
        var_name = item.text(0)
        
        # Konfirmasi hapus
        confirm = QMessageBox.question(
            self, "Delete Variable", 
            f"Are you sure you want to delete the variable '{var_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            self.var_manager.delete_global_variable(var_name)
            
            # Hapus dari visual pohon
            index = self.tree.indexOfTopLevelItem(item)
            self.tree.takeTopLevelItem(index)
    
    def on_item_changed(self, item, column):
        # Kita hanya urus jika yang berubah adalah kolom Nama (Index 0)
        # atau kolom lain yang butuh validasi
        self.tree.blockSignals(True)
        
        row_idx = self.tree.indexOfTopLevelItem(item)

        # Ambil list keys untuk mencari nama lama berdasarkan urutan row
        all_keys = list(self.var_manager.get_all_global_variables().keys())
        if row_idx >= len(all_keys): 
            self.tree.blockSignals(False)
            return
            
        old_name = all_keys[row_idx]
        new_name = None
        new_type = None

        # --- VALIDASI RENAME ---
        if column == 0:
            if new_name == "":
                item.setText(0, old_name) # Kembalikan jika kosong
                new_name = None
            elif new_name != old_name and self.var_manager.get_global_variable(new_name) is not None:
                QMessageBox.warning(self, "Rename Error", f"Name '{new_name}' is already in use!")
                item.setText(0, old_name) # Reset ke nama lama di visual
                new_name = None
            else:
                new_name = item.text(0)
        
        if column == 1:
            if item.text(1) != self.var_manager.get_global_variable(old_name).type:
                new_type = item.text(1)

        # --- UPDATE MANAGER ---
        new_data = Variable(
            type=new_type,
            value=None
        )
        
        self.var_manager.edit_global_variable(
            value_path=[old_name],
            new_name=new_name,
            new_data=new_data
        )
        self.tree.blockSignals(False)
    
    def handle_key_press(self, event):
        """Menangani tombol Delete pada keyboard"""
        if event.key() == Qt.Key.Key_Delete:
            selected_items = self.tree.selectedItems()
            for item in selected_items:
                self.delete_variable_item(item)
        else:
            # Tetap jalankan fungsi bawaan untuk navigasi panah dll
            QTreeWidget.keyPressEvent(self.tree, event)
    
    def show_context_menu(self, position):
        """Memunculkan menu klik kanan"""
        item = self.tree.itemAt(position)
        if not item: return

        menu = QMenu()
        act_rename = menu.addAction("Rename")
        act_edit = menu.addAction("Edit Value")
        menu.addSeparator()
        act_delete = menu.addAction("Delete")
        
        # Eksekusi menu
        action = menu.exec(self.tree.viewport().mapToGlobal(position))
        
        if action == act_rename:
            self.tree.editItem(item, 0) # Fokus edit pada kolom Name
        elif action == act_edit:
            self.tree.editItem(item, 2) # Fokus edit pada kolom Value
        elif action == act_delete:
            self.delete_variable_item(item)