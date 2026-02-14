from PyQt6.QtGui import QColor

from Core.Structures.Variable import Variable
from Core.Enums.DataType import DataType
from Core.VariableManager import VariableManager
from Core.Graph.BaseNode import BaseNode

class SetVarNode(BaseNode):
    def __init__(self):
        super().__init__("Set Variable")
        self.header_color = QColor(50, 150, 50, 200)
        self.var_manager = self.main_window.var_manager

        # 1. Socket Alur (Exec)
        self.add_socket(True, True)
        self.add_socket(False, True)

        self.in_data = None
        self.out_data = None

        self.properties = {
            "Variable": Variable(
                display_name="Variable",
                type=DataType.ENUM.value, 
                options=list(self.var_manager.get_all_global_variables().keys()),
                value=""
            ),
            "Value": Variable(
                display_name="Value",
                type=DataType.STRING.value,
                value=""
            )
        }
        
    def get_properties(self):
        return self.properties

    def set_property(self, key_path: list, value):
        super().set_property(key_path, value)
        
        # Pastikan field Value berubah sesuai tipe variabel
        if key_path[0] == "Variable":
            sel_var = self.var_manager.get_global_variable(self.properties["Variable"].value)
            val_data = Variable(
                type=DataType(sel_var.type).value,
                value=None,
                options=sel_var.options,
                element_type=sel_var.element_type
            )

            VariableManager.edit_variable(
                database=self.properties,
                value_path=["Value"],
                new_data=val_data)

        self.update_sockets_by_variable(self.properties["Variable"].value)
        self.update()

    def update_sockets_by_variable(self, var_name):
        """Membangun ulang atau menghapus socket data berdasarkan variabel"""
        self.selected_var = var_name
        var_info = self.var_manager.get_global_variable(var_name)

        if var_info:
            # Jika variabel valid, buat kembali socket datanya
            v_type = DataType(var_info.type)
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