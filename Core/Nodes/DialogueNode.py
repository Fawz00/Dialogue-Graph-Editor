from PyQt6.QtGui import QColor

from Core.BaseNode import BaseNode
from Core.Enums.DataType import DataType

class DialogueNode(BaseNode):
    def __init__(self):
        super().__init__("Dialogue")
        self.header_color = QColor(50, 100, 200, 200) # Biru
        self.npc_text = "Hello Traveler!"
        self.choices = ["Next"]
        
        self.add_socket(True, True) # Input flow
        self.refresh_outputs()

        self.properties = {
            "NPC Text": {
                "type": DataType.STRING,
                "value": self.npc_text
            },
            "Choices": {
                "type": DataType.STRING,
                "value": ",".join(self.choices) # Simpel: comma separated
            }
        }

    def refresh_outputs(self):
        # Hapus socket output lama (secara logika sederhana)
        # Di aplikasi real, perlu cleanup edge yang terhubung
        for s in self.outputs:
            self.scene().removeItem(s)
        self.outputs.clear()
        
        # Buat socket baru berdasarkan pilihan
        for choice in self.choices:
            self.add_socket(False, True, label=choice)

    def get_properties(self):
        return self.properties

    def set_property(self, key_path: list, value):
        if key_path[0] == "NPC Text":
            self.npc_text = value
        elif key_path[0] == "Choices":
            self.choices = [x.strip() for x in value.split(",") if x.strip()]
            self.refresh_outputs()