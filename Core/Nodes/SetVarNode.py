from PyQt6.QtGui import QColor

from Core.VariableManager import VariableManager
from Core.BaseNode import BaseNode

class SetVarNode(BaseNode):
    def __init__(self, var_manager):
        super().__init__("Set Variable")
        self.header_color = QColor(50, 150, 50, 200)
        self.var_manager = var_manager
        
        self.selected_var = ""
        self.value_to_set = "" # Inisialisasi awal agar tidak crash

        # 1. Socket Alur (Exec)
        self.add_socket(True, "exec")
        self.add_socket(False, "exec")

        self.in_data = None
        self.out_data = None
        
    def get_properties(self):
        # Pastikan list variabel selalu up-to-date
        var_names = list(self.var_manager.variables.keys()) if self.selected_var in self.var_manager.variables else [None]+list(self.var_manager.variables.keys())
        return {
            "Variable": {"type": "enum", "options": var_names, "value": self.selected_var},
            "Value": {"type": "text", "value": self.value_to_set}
        }

    def set_property(self, key, value):
        if key == "Variable":
            self.selected_var = value
            var_info = self.var_manager.variables.get(value)

            # Pastikan tidak invalid
            self.is_valid = var_info is not None

            if var_info:
                new_type = var_info['type']

                # Perbarui nilai default berdasarkan tipe variabel
                self.value_to_set = VariableManager.VAR_CONFIG[new_type]
        
        elif key == "Value":
            # Set nilai yang akan diassign ke variabel kalau ada
            self.value_to_set = value
            
        self.update_sockets_by_variable(value) # Perbarui socket data
        self.update()

    def update_sockets_by_variable(self, var_name):
        """Membangun ulang atau menghapus socket data berdasarkan variabel"""
        # Hapus socket data lama jika ada
        if self.in_data:
            self.remove_socket(self.in_data)
            self.in_data = None
        if self.out_data:
            self.remove_socket(self.out_data)
            self.out_data = None

        self.selected_var = var_name
        var_info = self.var_manager.variables.get(var_name)

        if var_info:
            # Jika variabel valid, buat kembali socket datanya
            v_type = var_info['type']
            self.title = f"Set {var_name}"
            self.in_data = self.add_socket(True, v_type, f"Value ({v_type})")
            self.out_data = self.add_socket(False, v_type, f"Out ({v_type})")
            self.is_valid = True

            self.in_data.update() # Refresh visual socket
            self.out_data.update()
        else:
            # Jika variabel dihapus/tidak ada
            self.title = "Set Variable (Select One)"
            self.selected_var = ""
            self.value_to_set = ""
            self.is_valid = False

            # Hapus semua socket data
            self.in_data = self.remove_socket(self.in_data) if self.in_data else None
            self.out_data = self.remove_socket(self.out_data) if self.out_data else None

        self.update() # Refresh visual node