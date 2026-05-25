from PyQt6.QtGui import QBrush, QPainter, QPen
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QStyleOptionGraphicsItem, QWidget

from Core.Graph.BaseNode import BaseNode
from Core.Enums.DataType import DataType
from Core.Graph.NodeRegistry import register_node
from Style import STYLES, DATA_TYPE_COLORS

@register_node
class RerouteNode(BaseNode):
    NODE_NAME = "Reroute"
    CATEGORY = ""

    def __init__(self, socket_data_type: DataType | None = None):
        super().__init__()
        self.radius = 16
        self.width = 20
        self.height = 20
        self.content_width = 5
        self.is_reroute = True
        self.is_removable = True
        
        # Hanya butuh satu input dan satu output
        if socket_data_type is not None:
            self.in_socket = self.add_data_socket(True, data_type=socket_data_type)
            self.out_socket = self.add_data_socket(False, data_type=socket_data_type)
        else:
            self.in_socket = self.add_exec_socket(True)
            self.out_socket = self.add_exec_socket(False)

    def paint(self, painter: QPainter | None, option: QStyleOptionGraphicsItem | None, widget: QWidget | None = None):
        # Visual reroute lebih simpel (hanya lingkaran kecil atau kotak)
        color = DATA_TYPE_COLORS.get(DataType(self.in_socket.data_type), STYLES['error']) if not self.in_socket.is_exec else STYLES['socket_exec']
        
        if painter is None:
            return
        
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(STYLES['node_sel_border'], 2) if self.isSelected() else QPen(Qt.PenStyle.NoPen))
        painter.drawEllipse(int(self.width/2)-int(self.radius/2)-0, int(self.height/2)-int(self.radius/2)+12, self.radius, self.radius)

    def update_type(self, is_exec: bool, new_type: DataType | None):
        """Mengubah tipe reroute mengikuti kabel yang terhubung"""
        self.in_socket.is_exec = is_exec
        self.out_socket.is_exec = is_exec

        if not self.in_socket.is_exec:
            self.in_socket.data_type = new_type
        else:
            self.in_socket.data_type = None

        if not self.out_socket.is_exec:
            self.out_socket.data_type = new_type
        else:
            self.out_socket.data_type = None
        
        # Refresh tampilan visual socket
        self.in_socket.update()
        self.out_socket.update()
    
    def sync_type(self, is_exec: bool, new_type: DataType | None):
        """Menyamakan tipe input dan output agar data bisa mengalir"""
        if self.in_socket.is_exec == is_exec:
            return # Sudah sesuai

        if self.in_socket.data_type == new_type:
            return # Sudah sesuai
            
        self.in_socket.data_type = new_type
        self.out_socket.data_type = new_type
        
        # Refresh tampilan visual socket
        self.in_socket.update()
        self.out_socket.update()
        self.update()