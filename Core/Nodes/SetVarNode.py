from PyQt6.QtGui import QColor

from Core.Structures.Property import Property
from Core.Enums.DataType import DataType
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
        self.add_socket(True, True)
        self.add_socket(False, True)

        self.in_data = None
        self.out_data = None
        
    def get_properties(self):
        # Pastikan list variabel selalu up-to-date
        var_names = list(self.var_manager.global_variables.keys()) if self.selected_var in self.var_manager.global_variables else [None]+list(self.var_manager.global_variables.keys())

        # properties = {
        #     "Variable": Property(type=DataType.ENUM.value, value=self.selected_var, options=var_names),
        #     "Advanced Settings": Property(
        #         type=DataType.STRUCT,
        #         value={
        #             "Priority": Property(type=DataType.INT.value, value=1),
        #             "Interpolate": Property(type=DataType.BOOL.value, value=False),
        #             "Test Float": Property(type=DataType.FLOAT.value, value=0.0),
        #             "Test List": Property(type=DataType.LIST.value, value=[]),
        #             "Text": Property(type=DataType.STRING.value, value="None")
        #         }
        #     )
        # }
        # return properties
        
        # return {
        #     "Variable": {
        #         "type": DataType.ENUM, 
        #         "options": var_names, 
        #         "value": self.selected_var
        #     },
        #     "Advanced Settings": {
        #         "type": DataType.STRUCT,
        #         "value": {
        #             "Priority": {"type": DataType.INT, "value": 1},
        #             "Interpolate": {"type": DataType.BOOL, "value": False},
        #             "Test Float": {"type": DataType.FLOAT, "value": 0.0},
        #             "Test List": {"type": DataType.LIST, "value": []},
        #             "Text": {"type": DataType.STRING, "value": "None"}
        #         }
        #     }
        # }

        return {
            "Variable": {
                "type": DataType.ENUM, 
                "options": var_names, 
                "value": self.selected_var
            },
            "Value": {
                "type": DataType(self.var_manager.global_variables[self.selected_var]['type']) if self.selected_var in self.var_manager.global_variables else DataType.STRING.value,
                "value": self.value_to_set
            }
        }

    def set_property(self, key, value):
        if key == "Variable":
            if self.selected_var == value:
                return

            self.selected_var = value
            var_info = self.var_manager.global_variables.get(value)

            # Pastikan tidak invalid
            self.is_valid = var_info is not None

            if var_info:
                new_type = var_info['type'] if isinstance(var_info['type'], DataType) else DataType(var_info['type'])

                # Perbarui nilai default berdasarkan tipe variabel
                self.value_to_set = VariableManager.DEFAULT_VALUES[new_type]
            
            self.update_sockets_by_variable(value) # Perbarui socket data
        
        elif key == "Value":
            # Set nilai yang akan diassign ke variabel kalau ada
            self.value_to_set = value
            
        self.update()

    def update_sockets_by_variable(self, var_name):
        """Membangun ulang atau menghapus socket data berdasarkan variabel"""
        self.selected_var = var_name
        var_info = self.var_manager.global_variables.get(var_name)

        if var_info:
            # Jika variabel valid, buat kembali socket datanya
            v_type = var_info['type']
            self.title = f"Set {var_name}"

            if self.in_data is None:
                self.in_data = self.add_socket(True, is_exec=False, data_type=v_type, label=f"Value ({v_type})")
            else:
                self.in_data = self.change_socket(self.in_data, is_exec=False, data_type=v_type)
            
            if self.out_data is None:
                self.out_data = self.add_socket(False, is_exec=False, data_type=v_type, label=f"Out ({v_type})")
            else:
                self.out_data = self.change_socket(self.out_data, is_exec=False, data_type=v_type)
            
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