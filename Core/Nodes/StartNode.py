from PyQt6.QtGui import QColor

from Core.Graph.BaseNode import BaseNode
from Core.Graph.NodeRegistry import register_node

@register_node
class StartNode(BaseNode):
    NODE_NAME = "Start"
    CATEGORY = "HIDDEN"

    def __init__(self):
        super().__init__()
        self.is_removable = False
        self.header_color = QColor(200, 50, 50, 200) # Merah
        self.add_socket(False, True) # Output only