from typing import Any

from PyQt6.QtGui import QColor

from Core.Graph.NodeRegistry import register_node
from Core.Structures.Variable import Variable
from Core.Graph.BaseNode import BaseNode
from Core.Enums.DataType import DataType

@register_node
class DialogueNode(BaseNode):
    NODE_NAME = "Dialogue"
    CATEGORY = "Dialogue"

    def __init__(self):
        super().__init__()
        self.header_color = QColor(50, 100, 200, 200) # Biru
        self.properties = {
            "speaker": Variable(
                display_name="Speaker",
                type=DataType.STRING,
                value=""
            ),
            "text": Variable(
                display_name="Dialogue Text",
                type=DataType.STRING,
                value=""
            ),
            "choices": Variable(
                display_name="Choices",
                type=DataType.ARRAY,
                element_type=DataType.STRING,
                value=[""] # Mulai dengan satu pilihan kosong
            )
        }
        
        self.add_socket(True, True) # Input flow
        self._setup_inline_editors()
        self.refresh_outputs()

    def refresh_outputs(self):
        # Hapus socket output lama (secara logika sederhana)
        # Di aplikasi real, perlu cleanup edge yang terhubung
        for s in self.outputs:
            scene = self.scene()
            if scene is not None:
                scene.removeItem(s)
        self.outputs.clear()
        
        # Buat socket baru berdasarkan pilihan
        if isinstance(self.properties["choices"].value, list): # Expected: list[str]
            for choice in self.properties["choices"].value:
                if isinstance(choice, str):
                    self.add_socket(False, True, label=choice)

    def get_properties(self):
        return self.properties

    def set_property(self, key_path: list[str], value: Any):        
        super().set_property(key_path, value)

        if key_path[0] == "choices":
            self.refresh_outputs()
    
    def _setup_inline_editors(self):
        speaker = self.add_socket(True, False, DataType.STRING)
        text = self.add_socket(True, False, DataType.STRING)
        choices = self.add_socket(True, False, DataType.ARRAY)

        self.add_inline_input(speaker, "speaker")
        self.add_inline_input(text, "text")
        self.add_inline_input(choices, "choices")