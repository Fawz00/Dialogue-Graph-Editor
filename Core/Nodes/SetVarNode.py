from typing import Any

from PyQt6.QtGui import QColor

from Core.Structures.Variable import Variable
from Core.Enums.DataType import DataType
from Core.VariableManager import VariableManager
from Core.Graph.BaseNode import BaseNode

class SetVarNode(BaseNode):
    def __init__(self):
        super().__init__("Set Variable")
        self.header_color = QColor(50, 150, 50, 200)
        self.var_manager = self.main_window.var_manager if self.main_window else None

        # 1. Socket Alur (Exec)
        self.add_socket(True, True)
        self.add_socket(False, True)

        self.in_data = None
        self.out_data = None

        self.properties = {
            "Variable": Variable(
                display_name="Variable",
                type=DataType.ENUM, 
                options=list(self.var_manager.get_all_global_variables().keys()) if self.var_manager else [],
                value=""
            ),
            "Value": Variable(
                display_name="Value",
                type=DataType.STRING,
                value=""
            )
        }
        
    def get_properties(self):
        return self.properties

    def set_property(self, key_path: list[str], value: Any):
        super().set_property(key_path, value)

        # Pastikan field Value berubah sesuai tipe variabel
        if key_path[0] == "Variable":
            var_name = self.properties["Variable"].value if isinstance(self.properties["Variable"].value, str) else ""
            sel_var = self.var_manager.get_global_variable(var_name) if self.var_manager else None
            if sel_var is not None:
                val_data = Variable(
                    type=DataType(sel_var.type),
                    value=None,
                    options=sel_var.options,
                    element_type=sel_var.element_type
                )
                VariableManager.edit_variable(
                    database=self.properties,
                    value_path=["Value"],
                    new_data=val_data)
                
            else:
                # If variable is deleted, reset Value property to default string
                val_data = Variable(
                    display_name="Value",
                    type=DataType.STRING,
                    value=""
                )
                VariableManager.edit_variable(
                    database=self.properties,
                    value_path=["Value"],
                    new_data=val_data)

        var_name = self.properties["Variable"].value if isinstance(self.properties["Variable"].value, str) else ""
        self.update_sockets_by_variable(var_name)
        self.update()

    def update_sockets_by_variable(self, var_name: str):
        """Membangun ulang atau menghapus socket data berdasarkan variabel"""
        self.selected_var = var_name
        var_info = self.var_manager.get_global_variable(var_name) if self.var_manager else None

        VariableManager.edit_variable(
            database=self.properties,
            value_path=["Variable"],
            new_data=Variable(
                type=DataType.ENUM,
                options=list(self.var_manager.get_all_global_variables().keys()) if self.var_manager else [],
                value=self.properties["Variable"].value
            )
        )

        if var_info:
            # Jika variabel valid, buat kembali socket datanya
            v_type = DataType(var_info.type)
            self.title = f"Set {var_name}"

            if self.in_data is None:
                self.in_data = self.add_socket(True, is_exec=False, data_type=v_type, label=f"Value ({v_type.value})", prop_reference_path=["Value"])
            else:
                self.in_data = self.change_socket(self.in_data, is_exec=False, data_type=v_type, label=f"Value ({v_type.value})", prop_reference_path=["Value"])
            
            if self.out_data is None:
                self.out_data = self.add_socket(False, is_exec=False, data_type=v_type, label=f"Out ({v_type.value})", prop_reference_path=["Value"])
            else:
                self.out_data = self.change_socket(self.out_data, is_exec=False, data_type=v_type, label=f"Out ({v_type.value})", prop_reference_path=["Value"])
            
            self.is_valid = True

            self.in_data.update() # Refresh visual socket
            self.out_data.update()
        else:
            # Jika variabel dihapus/tidak ada
            self.title = "Set Variable [Error]"
            self.selected_var = ""
            self.value_to_set = ""
            self.is_valid = False

            # Hapus semua socket data
            self.in_data = self.remove_socket(self.in_data) if self.in_data else None
            self.out_data = self.remove_socket(self.out_data) if self.out_data else None

        self.update() # Refresh visual node