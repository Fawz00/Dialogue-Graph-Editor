from __future__ import annotations
from typing import TYPE_CHECKING

from PyQt6.QtWidgets import (QGraphicsPathItem)
from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import QPen, QPainterPath

from Core.Enums.DataType import DataType
from Style import STYLES, DATA_TYPE_COLORS

if TYPE_CHECKING:
    from Core.Graph.SocketItem import SocketItem

class EdgeItem(QGraphicsPathItem):
    def __init__(self, start_socket: SocketItem, end_socket: SocketItem, cur_mouse_pos: QPointF | None = None):
        super().__init__()
        self.setZValue(-1) # Gambar di belakang node
        self.start_socket = start_socket
        self.end_socket = end_socket
        self.cur_mouse_pos: QPointF = cur_mouse_pos if cur_mouse_pos is not None else start_socket.get_scene_pos()
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
        color = DATA_TYPE_COLORS.get(DataType(self.start_socket.data_type), Qt.GlobalColor.white) if not self.start_socket.is_exec else STYLES['socket_exec']
        
        # Kabel EXEC lebih tebal (3px), Kabel DATA lebih tipis (2px)
        width = 3 if self.start_socket.is_exec else 2
        
        pen = QPen(color, width)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap) # Membuat ujung kabel tumpul/rapi
        self.setPen(pen)