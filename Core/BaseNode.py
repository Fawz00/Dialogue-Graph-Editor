import sys
from PyQt6.QtWidgets import (QGraphicsItem, QSizePolicy)
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPen, QPainterPath, QFont
from typing import cast

from Style import STYLES
from Core.Graph.SocketItem import SocketItem

class BaseNode(QGraphicsItem):
    def __init__(self, title="Node"):
        super().__init__()
        self.title = title
        self.is_removable = True
        self.is_valid = True
        self.properties = {}
        self.width = 150
        self.height = 80

        # Sockets
        self.inputs = []
        self.outputs = []
        
        # Flags
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        
        # Header Color (bisa di override per tipe node)
        self.header_color = STYLES['node_header']

    def boundingRect(self):
        return QRectF(-8, -8, self.width+16, self.height+16) # Sedikit lebih besar untuk border seleksi

    def paint(self, painter, option, widget):
        # Soft shadow
        painter.save()

        painter.setPen(QPen(Qt.PenStyle.NoPen))
        painter.setBrush(STYLES['node_shadow'])

        dx, dy = 0, 0          # arah
        layers = 4             # jangkauan
        base_opacity = 0.1    # intensitas dekat objek
        spread_step = 2        # seberapa cepat melebar
        falloff = 0.6          # semakin besar → cepat hilang

        for i in range(layers):
            t = i + 1
            painter.setOpacity(base_opacity / (t ** falloff))

            expand = i * spread_step
            painter.drawRoundedRect(
                dx - expand,
                dy - expand,
                self.width + expand * 2,
                self.height + expand * 2,
                12,
                12
            )

        painter.restore()

        # Body
        painter.setBrush(STYLES['node_body'])
        pen = QPen(STYLES['node_sel_border'], 2) if self.isSelected() else (QPen(STYLES['invalid_node_border'], 2) if not self.is_valid else QPen(Qt.PenStyle.NoPen))
        painter.setPen(pen)
        painter.drawRoundedRect(0, 0, self.width, self.height, 10, 10)
        
        # Header
        path = QPainterPath()
        path.setFillRule(Qt.FillRule.WindingFill)
        path.addRoundedRect(0, 0, self.width, 30, 10, 10)
        # Hack untuk membuat bawah header rata (menutup rounded corner bawah)
        rect_fix = QRectF(0, 20, self.width, 10) 
        path.addRect(rect_fix)
        
        painter.setBrush(self.header_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPath(path.simplified())

        # Title Text
        painter.setPen(STYLES['text_color'])
        painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        painter.drawText(QRectF(10, 0, self.width-20, 30), Qt.AlignmentFlag.AlignVCenter, self.title)

    def add_socket(self, is_input, is_exec=True, data_type=None, label=""):
        socket = SocketItem(self, len(self.inputs) if is_input else len(self.outputs), is_input, is_exec=is_exec, data_type=data_type, label=label)
        if is_input:
            self.inputs.append(socket)
        else:
            self.outputs.append(socket)
        self.update_socket_positions()
        return socket

    def change_socket(self, socket, is_exec=True, data_type=None, label=""):
        """Mengganti properti socket tanpa menghapusnya"""
        socket.change_type(is_exec=is_exec, data_type=data_type, label=label)
        self.update_socket_positions()
        return socket

    def remove_socket(self, socket):
        """Menghapus socket secara bersih dari list dan scene"""
        if socket in self.inputs:
            self.inputs.remove(socket)
        if socket in self.outputs:
            self.outputs.remove(socket)
        
        socket.destroy()
        
        self.update_socket_positions()

    def update_socket_positions(self):
        # Hitung tinggi node berdasarkan jumlah socket
        count_in = len(self.inputs)
        count_out = len(self.outputs)
        max_sockets = max(count_in, count_out)
        
        self.height = max(80, 40 + (max_sockets * 25))
        
        y_start = 45
        for i, sock in enumerate(self.inputs):
            sock.setPos(0, y_start + (i * 25))
            
        for i, sock in enumerate(self.outputs):
            sock.setPos(self.width, y_start + (i * 25))
            
        self.update() # Redraw

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            # Update edges connected to this node
            for sock in self.inputs + self.outputs:
                for edge in sock.edges:
                    edge.update_path()
        return super().itemChange(change, value)

    def refresh(self):
        """Override ini untuk memperbarui tampilan atau data internal node"""
        pass

    def get_properties(self) -> dict:
        """Override ini untuk menampilkan properti di panel samping"""
        return {}

    def set_property(self, key_path: list, value):
        """Override ini untuk menerima update dari panel samping"""
        pass

    def serialize(self):
        """Mengubah node menjadi dict untuk disimpan"""
        return {
            "id": id(self),
            "title": self.title,
            "pos": (self.pos().x(), self.pos().y()),
            "node_type": self.__class__.__name__,
            "properties": self.properties,
            "sockets": {
                "inputs": [sock.serialize() for sock in self.inputs],
                "outputs": [sock.serialize() for sock in self.outputs]
            }
        }
