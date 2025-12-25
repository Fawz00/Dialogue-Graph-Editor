from PyQt6.QtGui import QColor

from Core.BaseNode import BaseNode

class DialogueNode(BaseNode):
    def __init__(self):
        super().__init__("Dialogue")
        self.header_color = QColor(50, 100, 200, 200) # Biru
        self.npc_text = "Hello Traveler!"
        self.choices = ["Next"]
        
        self.add_socket(True, "exec") # Input flow
        self.refresh_outputs()

    def refresh_outputs(self):
        # Hapus socket output lama (secara logika sederhana)
        # Di aplikasi real, perlu cleanup edge yang terhubung
        for s in self.outputs:
            self.scene().removeItem(s)
        self.outputs.clear()
        
        # Buat socket baru berdasarkan pilihan
        for choice in self.choices:
            self.add_socket(False, "exec", choice)

    def get_properties(self):
        return {
            "NPC Text": {"type": "text", "value": self.npc_text},
            "Choices": {"type": "list", "value": ",".join(self.choices)} # Simpel: comma separated
        }

    def set_property(self, key, value):
        if key == "NPC Text":
            self.npc_text = value
        elif key == "Choices":
            self.choices = [x.strip() for x in value.split(",") if x.strip()]
            self.refresh_outputs()