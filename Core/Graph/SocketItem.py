from PyQt6.QtWidgets import (QGraphicsItem)
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QBrush, QFont, QPainterPath, QPen, QColor

from Style import STYLES, TYPE_COLORS

class SocketItem(QGraphicsItem):
    def __init__(self, parent_node, index, is_input=True, socket_type="exec", label=""):
        super().__init__(parent_node)
        self.parent_node = parent_node
        self.index = index
        self.is_input = is_input
        self.socket_type = socket_type  # "exec", "string", "int", etc.
        self.label = label
        self.collision_radius = 8
        self.radius = 6
        self.edges = []
        self.setAcceptHoverEvents(True)
        
        # Posisi relatif terhadap node akan diatur oleh node itu sendiri
        self.setAcceptHoverEvents(True)

    def boundingRect(self):
        return QRectF(-self.collision_radius, -self.collision_radius, self.collision_radius*2, self.collision_radius*2)

    def paint(self, painter, option, widget):
        # Ambil warna berdasarkan tipe data
        color = TYPE_COLORS.get(self.socket_type, QColor(200, 200, 200))
        
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(Qt.GlobalColor.black, 1))
        
        # Gambar bentuk Polygon (Segitiga/Pentagon) jika EXEC, Lingkaran jika DATA
        if self.socket_type == "exec":
            path = QPainterPath()
            path.moveTo(-5, -5)
            path.lineTo(5, 0)
            path.lineTo(-5, 5)
            path.closeSubpath()
            painter.drawPath(path)
        else:
            painter.drawEllipse(-self.radius, -self.radius, self.radius*2, self.radius*2)
        
        # Label (Tetap sama)
        if self.label:
            painter.setPen(STYLES['text_color'])
            painter.setFont(QFont("Arial", 8))
            text_rect = QRectF(12 if self.is_input else -102, -5, 90, 20)
            align = Qt.AlignmentFlag.AlignLeft if self.is_input else Qt.AlignmentFlag.AlignRight
            painter.drawText(text_rect, align, self.label)

    def get_scene_pos(self):
        return self.mapToScene(0, 0)