import sys
from PyQt6.QtWidgets import (QMessageBox, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, 
                             QPushButton, QComboBox, QTreeWidget, QTreeWidgetItem, QMenu)
from PyQt6.QtCore import Qt, pyqtSignal, QObject

from Core.Enums.DataType import DataType
from Core.Nodes.SetVarNode import SetVarNode
from Core.VariableManager import VariableManager
from Core.UIPanel.Utils.TypeDelegate import TypeDelegate

class GlobalVariablePanel(QWidget):
    variable_changed = pyqtSignal(str, str)  # old_name, new_name
    
    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        self.layout = QVBoxLayout(self)
        
        # UI Create Section
        form = QHBoxLayout()
        self.name_edit = QLineEdit(placeholderText="Variable Name")
        self.type_combo = QComboBox()
        self.type_combo.addItems(VariableManager.SUPPORTED_TYPES)
        btn_add = QPushButton("+ Add")
        btn_add.clicked.connect(self.add_variable)
        form.addWidget(self.name_edit); form.addWidget(self.type_combo); form.addWidget(btn_add)
        self.layout.addLayout(form)
        
        # Tree/Table Section
        self.tree = QTreeWidget()
        self.tree.setColumnCount(3)
        self.tree.setHeaderLabels(["Name", "Type", "Default Value"])
        
        # PASANG DROPDOWN KE KOLOM TYPE (Index 1)
        self.tree.setItemDelegateForColumn(1, TypeDelegate(self))

        # Aktifkan Context Menu
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)
        
        # Hubungkan event key press
        self.tree.keyPressEvent = self.handle_key_press
        
        self.tree.itemChanged.connect(self.on_item_changed)
        self.layout.addWidget(self.tree)

    def add_variable(self):
        name = self.name_edit.text().strip()
        if not name: return
        
        # Validasi: Cek apakah nama sudah ada
        if name in self.manager.global_variables:
            QMessageBox.warning(self, "Duplicate Name", f"Variable with name '{name}' already exists!")
            self.name_edit.setStyleSheet("background-color: #ffcccc;") # Feedback merah
            return

        self.name_edit.setStyleSheet("") # Reset style jika berhasil
        v_type = self.type_combo.currentText()
        default_val = VariableManager.DEFAULT_VALUES[DataType(v_type)]
        
        self.manager.global_variables[name] = {'type': v_type, 'value': default_val}
        
        item = QTreeWidgetItem([name, v_type, str(default_val)])
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
        self.tree.addTopLevelItem(item)
        self.name_edit.clear()
        
        # Emit signal created
        self.manager.variable_created.emit(name)
    
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
            if var_name in self.manager.global_variables:
                del self.manager.global_variables[var_name]
                # Emit signal agar Graph & Details ikut update
                self.manager.variable_deleted.emit(var_name)
            
            # Hapus dari visual pohon
            index = self.tree.indexOfTopLevelItem(item)
            self.tree.takeTopLevelItem(index)
    
    def on_item_changed(self, item, column):
        # Kita hanya urus jika yang berubah adalah kolom Nama (Index 0)
        # atau kolom lain yang butuh validasi
        self.tree.blockSignals(True)
        
        row_idx = self.tree.indexOfTopLevelItem(item)

        # Ambil list keys untuk mencari nama lama berdasarkan urutan row
        all_keys = list(self.manager.global_variables.keys())
        if row_idx >= len(all_keys): 
            self.tree.blockSignals(False)
            return
            
        old_name = all_keys[row_idx]
        new_name = item.text(0).strip()
        new_type = item.text(1)
        new_val_str = item.text(2)

        # --- VALIDASI RENAME ---
        if column == 0:
            if new_name == "":
                item.setText(0, old_name) # Kembalikan jika kosong
                new_name = old_name
            elif new_name != old_name and new_name in self.manager.global_variables:
                QMessageBox.warning(self, "Rename Error", f"Name '{new_name}' is already in use!")
                item.setText(0, old_name) # Reset ke nama lama di visual
                new_name = old_name
            
        # --- LOGIKA KONVERSI (Seperti sebelumnya) ---
        # ... (Gunakan logika konversi DEFAULT_VALUES yang kita buat tadi) ...
        # Misal:
        converted_val = VariableManager.DEFAULT_VALUES[DataType(new_type)]
        try:
            if DataType(new_type) == DataType.INT: converted_val = int(float(new_val_str))
            elif DataType(new_type) == DataType.FLOAT: converted_val = float(new_val_str)
            elif DataType(new_type) == DataType.BOOL: converted_val = new_val_str in ("1", "True", "Yes", "true", "yes", "T", "Y", "t", "y")
            elif DataType(new_type) == DataType.STRING: converted_val = new_val_str
            # dst...
        except:
            pass
        item.setText(2, str(converted_val))

        # --- UPDATE MANAGER ---
        if old_name != new_name:
            # Pindahkan data ke key baru
            self.manager.global_variables[new_name] = self.manager.global_variables.pop(old_name)
            self.manager.global_variables[new_name]['type'] = new_type
            self.manager.global_variables[new_name]['value'] = converted_val

            # Emit signal update
            self.manager.variable_updated.emit(old_name, new_name)
        else:
            # Update tipe/value saja
            self.manager.global_variables[old_name]['type'] = new_type
            self.manager.global_variables[old_name]['value'] = converted_val

            # Emit signal update dengan nama lama (karena tidak berubah)
            self.manager.variable_updated.emit(old_name, old_name)

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