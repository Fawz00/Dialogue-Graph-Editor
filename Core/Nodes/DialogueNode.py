from PyQt6.QtGui import QColor

from Core.Structures.Variable import Variable
from Core.BaseNode import BaseNode
from Core.Enums.DataType import DataType
from Core.VariableManager import VariableManager

class DialogueNode(BaseNode):
    def __init__(self):
        super().__init__("Dialogue")
        self.header_color = QColor(50, 100, 200, 200) # Biru
        self.properties = {
            "speaker": Variable(
                display_name="Speaker",
                type=DataType.STRING.value,
                value=""
            ),
            "text": Variable(
                display_name="Dialogue Text",
                type=DataType.STRING.value,
                value=""
            ),
            "choices": Variable(
                display_name="Choices",
                type=DataType.ARRAY.value,
                element_type=DataType.STRING.value,
                value=[""] # Mulai dengan satu pilihan kosong
            )
        }
        
        self.add_socket(True, True) # Input flow
        self.refresh_outputs()

    def refresh_outputs(self):
        # Hapus socket output lama (secara logika sederhana)
        # Di aplikasi real, perlu cleanup edge yang terhubung
        for s in self.outputs:
            self.scene().removeItem(s)
        self.outputs.clear()
        
        # Buat socket baru berdasarkan pilihan
        for choice in self.properties["choices"].value:
            self.add_socket(False, True, label=choice)

    def get_properties(self):
        return self.properties

    def set_property(self, key_path: list, value):
        VariableManager.edit_variable(
            database=self.properties,
            value_path=key_path,
            new_data=Variable(
                type=None,
                value=value
            )
        )

        if key_path[0] == "choices":
            self.refresh_outputs()