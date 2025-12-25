from PyQt6.QtGui import QColor, QBrush, QPen
from PyQt6.QtCore import Qt

from Core.BaseNode import BaseNode
from Style import STYLES, TYPE_COLORS

class RerouteNode(BaseNode):
    def __init__(self, socket_type="exec"):
        super().__init__("Reroute")
        self.radius = 16
        self.width = 20
        self.height = 20
        self.is_reroute = True
        self.is_removable = True
        
        # Hanya butuh satu input dan satu output
        self.in_socket = self.add_socket(True, socket_type)
        self.out_socket = self.add_socket(False, socket_type)

    def paint(self, painter, option, widget):
        # Visual reroute lebih simpel (hanya lingkaran kecil atau kotak)
        color = TYPE_COLORS.get(self.in_socket.socket_type, QColor(200, 200, 200))
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(STYLES['node_sel_border'], 2) if self.isSelected() else QPen(Qt.PenStyle.NoPen))
        painter.drawEllipse(int(self.width/2)-int(self.radius/2)-0, int(self.height/2)-int(self.radius/2)+4, self.radius, self.radius)

    def update_type(self, new_type):
        """Mengubah tipe reroute mengikuti kabel yang terhubung"""
        self.in_socket.socket_type = new_type
        self.out_socket.socket_type = new_type
        self.in_socket.update()
        self.out_socket.update()
    
    def sync_type(self, new_type):
        """Menyamakan tipe input dan output agar data bisa mengalir"""
        if self.in_socket.socket_type == new_type:
            return # Sudah sesuai
            
        self.in_socket.socket_type = new_type
        self.out_socket.socket_type = new_type
        
        # Refresh tampilan visual socket
        self.in_socket.update()
        self.out_socket.update()
        self.update()