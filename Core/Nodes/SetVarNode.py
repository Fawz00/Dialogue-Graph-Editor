from PyQt6.QtGui import QColor

from Core.Structures.Property import Property
from Core.Enums.DataType import DataType
from Core.VariableManager import VariableManager
from Core.BaseNode import BaseNode

class SetVarNode(BaseNode):
    def __init__(self, var_manager: VariableManager):
        super().__init__("Set Variable")
        self.header_color = QColor(50, 150, 50, 200)
        self.var_manager = var_manager

        # 1. Socket Alur (Exec)
        self.add_socket(True, True)
        self.add_socket(False, True)

        self.in_data = None
        self.out_data = None

        self.properties = {
            "Variable": {
                "type": DataType.ENUM, 
                "options": self.var_manager.global_variables.keys(),
                "value": ""
            },
            "Value": {
                "type": DataType.STRING,
                "value": ""
            }
        }
        
    def get_properties(self):        
        # properties = {
        #     "Variable": Property(type=DataType.ENUM.value, value=self.selected_var, options=var_names),
        #     "Advanced Settings": Property(
        #         type=DataType.STRUCT,
        #         value={
        #             "Priority": Property(type=DataType.INT.value, value=1),
        #             "Interpolate": Property(type=DataType.BOOL.value, value=False),
        #             "Test Float": Property(type=DataType.FLOAT.value, value=0.0),
        #             "Test Array": Property(type=DataType.ARRAY.value, value=[]),
        #             "Text": Property(type=DataType.STRING.value, value="None")
        #         }
        #     )
        # }
        # return properties

        return self.properties

    def set_property(self, key_path: list, value):
        if key_path[0] == "Variable":
            if self.properties["Variable"]["value"] == value:
                return

            self.properties["Variable"]["value"] = value
            var_info = self.var_manager.global_variables.get(value)

            # Pastikan tidak invalid
            self.is_valid = var_info is not None

            if self.is_valid:
                new_type = DataType(var_info['type'])

                # Perbarui nilai default berdasarkan tipe variabel
                self.properties["Value"]["type"] = new_type
                self.properties["Value"]["value"] = VariableManager.get_default_value(new_type)
            
            self.update_sockets_by_variable(value) # Perbarui socket data
        
        elif key_path[0] == "Value":
            # Set nilai yang akan diassign ke variabel kalau ada
            self.properties["Value"]["value"] = value
            
        self.update()

    def update_sockets_by_variable(self, var_name):
        """Membangun ulang atau menghapus socket data berdasarkan variabel"""
        self.selected_var = var_name
        var_info = self.var_manager.global_variables.get(var_name)

        if var_info:
            # Jika variabel valid, buat kembali socket datanya
            v_type = DataType(var_info['type'])
            self.title = f"Set {var_name}"

            if self.in_data is None:
                self.in_data = self.add_socket(True, is_exec=False, data_type=v_type, label=f"Value ({v_type.value})")
            else:
                self.in_data = self.change_socket(self.in_data, is_exec=False, data_type=v_type, label=f"Value ({v_type.value})")
            
            if self.out_data is None:
                self.out_data = self.add_socket(False, is_exec=False, data_type=v_type, label=f"Out ({v_type.value})")
            else:
                self.out_data = self.change_socket(self.out_data, is_exec=False, data_type=v_type, label=f"Out ({v_type.value})")
            
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