from PyQt6.QtGui import QColor

from Core.Structures.Variable import Variable
from Core.BaseNode import BaseNode
from Core.Enums.DataType import DataType

class DialogueNode(BaseNode):
    def __init__(self):
        super().__init__("Dialogue")
        self.header_color = QColor(50, 100, 200, 200) # Biru
        self.properties = {
            "dialogue_speaker": Variable(
                display_name="Speaker",
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
        if key_path[0] == "dialogue_speaker":
            self.properties["dialogue_speaker"].value = value

        elif key_path[0] == "choices":
            self.properties["choices"].value = [x.strip() for x in value.split(",") if x.strip()]
            self.refresh_outputs()