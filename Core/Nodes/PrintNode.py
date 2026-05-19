from PyQt6.QtGui import QColor

from Core.Debug import Debug
from Core.Enums.DataType import DataType
from Core.Graph.BaseNode import BaseNode
from Core.Graph.SocketItem import SocketItem
from Core.Structures.Variable import Variable
from Core.VariableManager import VariableManager

class PrintNode(BaseNode):
    def __init__(self):
        super().__init__("Print")
        self.header_color = QColor(50, 50, 200, 200)
        self.var_manager = self.main_window.var_manager
        self.add_socket(True, True)
        self.add_socket(False, True)

        self.in_data = None

        self.properties = {
            "out": Variable(
                display_name="Text to Print",
                type=DataType.STRING,
                value=""
            )
        }
    
    def get_properties(self):
        return self.properties

    def set_property(self, key_path: list, value):
        super().set_property(key_path, value)

        if key_path[0] == "out" and isinstance(value, str):
            val_data = Variable(
                    type=DataType.STRING,
                    value=value
                )
            VariableManager.edit_variable(
                database=self.properties,
                value_path=["out"],
                new_data=val_data)

        self.update()
    
    def execute(self) -> SocketItem:
        Debug.log(f"{self.properties['out'].value}")
        return self.outputs[0]  # Return the output socket