from PyQt6.QtGui import QColor

from Core.BaseNode import BaseNode

class StartNode(BaseNode):
    def __init__(self):
        super().__init__("Start")
        self.is_removable = False
        self.header_color = QColor(200, 50, 50, 200) # Merah
        self.add_socket(False, True) # Output only