from PyQt6.QtGui import QColor, QBrush, QPen
from PyQt6.QtCore import Qt

from Core.Graph.BaseNode import BaseNode
from Core.Enums.DataType import DataType
from Style import STYLES, DATA_TYPE_COLORS

class RerouteNode(BaseNode):
    def __init__(self, is_exec=True, socket_data_type=None):
        super().__init__("Reroute")
        self.radius = 16
        self.width = 20
        self.height = 20
        self.content_width = 5
        self.is_reroute = True
        self.is_removable = True
        
        # Hanya butuh satu input dan satu output
        self.in_socket = self.add_socket(True, is_exec=is_exec, data_type=socket_data_type)
        self.out_socket = self.add_socket(False, is_exec=is_exec, data_type=socket_data_type)

    def paint(self, painter, option, widget):
        # Visual reroute lebih simpel (hanya lingkaran kecil atau kotak)
        color = DATA_TYPE_COLORS.get(DataType(self.in_socket.data_type), STYLES['error']) if not self.in_socket.is_exec else STYLES['socket_exec']
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(STYLES['node_sel_border'], 2) if self.isSelected() else QPen(Qt.PenStyle.NoPen))
        painter.drawEllipse(int(self.width/2)-int(self.radius/2)-0, int(self.height/2)-int(self.radius/2)+12, self.radius, self.radius)

    def update_type(self, is_exec, new_type):
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
    
    def sync_type(self, is_exec, new_type):
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