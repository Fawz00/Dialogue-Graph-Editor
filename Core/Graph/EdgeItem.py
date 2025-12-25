import sys
from PyQt6.QtWidgets import (QGraphicsPathItem)
from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import QPen, QPainterPath

from Style import STYLES, TYPE_COLORS

class EdgeItem(QGraphicsPathItem):
    def __init__(self, start_socket, end_socket=None, cur_mouse_pos=None):
        super().__init__()
        self.setZValue(-1) # Gambar di belakang node
        self.start_socket = start_socket
        self.end_socket = end_socket
        self.cur_mouse_pos = cur_mouse_pos if cur_mouse_pos else start_socket.get_scene_pos()
        self.update_path()

    def update_path(self):
        start_pos = self.start_socket.get_scene_pos()
        end_pos = self.end_socket.get_scene_pos() if self.end_socket else self.cur_mouse_pos

        path = QPainterPath()
        path.moveTo(start_pos)

        # Logic Bezier Curve ala Unreal Engine
        dx = abs(end_pos.x() - start_pos.x())
        ctrl1 = QPointF(start_pos.x() + dx * 0.5, start_pos.y())
        ctrl2 = QPointF(end_pos.x() - dx * 0.5, end_pos.y())
        
        path.cubicTo(ctrl1, ctrl2, end_pos)
        self.setPath(path)

        # Style garis
        color = TYPE_COLORS.get(self.start_socket.socket_type, Qt.GlobalColor.white)
        
        # Kabel EXEC lebih tebal (3px), Kabel DATA lebih tipis (2px)
        width = 3 if self.start_socket.socket_type == "exec" else 2
        
        pen = QPen(color, width)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap) # Membuat ujung kabel tumpul/rapi
        self.setPen(pen)