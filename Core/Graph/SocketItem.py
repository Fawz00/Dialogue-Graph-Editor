from PyQt6.QtWidgets import (QGraphicsItem)
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QBrush, QFont, QPainterPath, QPen, QColor
from typing import cast

from Core.Enums.DataType import DataType
from Core.Graph.EdgeItem import EdgeItem
from Style import STYLES, DATA_TYPE_COLORS

class SocketItem(QGraphicsItem):
    def __init__(self, parent_node, index, is_input=True, is_exec=True, data_type: DataType = None, label=""):
        super().__init__(parent_node)
        self.parent_node = parent_node
        self.index = index
        self.is_input = is_input
        self.is_exec = is_exec
        self.data_type = data_type
        self.label = label
        self.collision_radius = 8
        self.radius = 6
        self.edges: list[EdgeItem] = []
        self.setAcceptHoverEvents(True)
        
        # Posisi relatif terhadap node akan diatur oleh node itu sendiri
        self.setAcceptHoverEvents(True)

    def boundingRect(self):
        return QRectF(-self.collision_radius, -self.collision_radius, self.collision_radius*2, self.collision_radius*2)

    def paint(self, painter, option, widget):
        # Ambil warna berdasarkan tipe data
        color = DATA_TYPE_COLORS.get(DataType(self.data_type), QColor(150, 150, 150)) if not self.is_exec else STYLES['socket_exec']
        
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(Qt.GlobalColor.black, 1))
        
        # Gambar bentuk Polygon (Segitiga/Pentagon) jika EXEC, Lingkaran jika DATA
        if self.is_exec:
            path = QPainterPath()
            path.moveTo(-6, -6)
            path.lineTo(0, -6)
            path.lineTo(6, 0)
            path.lineTo(0, 6)
            path.lineTo(-6, 6)
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
    
    def change_type(self, is_exec, data_type, label=""):
        """Mengganti properti socket tanpa menghapusnya"""

        if self.is_exec != is_exec or self.data_type != data_type:
            # Putuskan semua koneksi yang ada karena tipenya berubah
            self.clear_connections()

        self.is_exec = is_exec
        self.data_type = data_type if not is_exec else None
        self.label = label if label != "" else self.label
        self.update()
    
    def connect_to(self, target_sock):
        """
        Aturan yang diterapkan:
        1. Output Exec: SINGLE
        2. Input Exec:  MULTI (Banyak kabel bisa masuk)
        3. Output Data: MULTI
        4. Input Data:  SINGLE
        """
        current_sock = self

        # Note: `start_sock.parent_node` type == RerouteNode

        # --- Logika Adaptasi Reroute ---
        # Jika salah satu socket milik RerouteNode, samakan tipenya
        if hasattr(current_sock.parent_node, 'is_reroute'):
            current_sock.parent_node.sync_type(target_sock.is_exec, target_sock.data_type)
        elif hasattr(target_sock.parent_node, 'is_reroute'):
            target_sock.parent_node.sync_type(current_sock.is_exec, current_sock.data_type)
        
        # --- LOGIKA SINGLE CONNECTION (PEMBERSIHAN) ---
        
        # Jika START (Output) adalah Exec, dia harus single. 
        # Putuskan kabel lama yang keluar dari dia.
        if not current_sock.is_input and current_sock.is_exec:
            current_sock.clear_connections()

        # Jika END (Input) adalah Data (Bukan Exec), dia harus single.
        # Putuskan kabel lama yang masuk ke dia.
        if target_sock.is_input and not target_sock.is_exec:
            target_sock.clear_connections()

        # Fitur Tambahan: Jika salah satu adalah Reroute, sesuaikan tipenya
        if hasattr(current_sock.parent_node, 'is_reroute'):
            current_sock.parent_node.update_type(target_sock.is_exec, target_sock.data_type)
        elif hasattr(target_sock.parent_node, 'is_reroute'):
            target_sock.parent_node.update_type(current_sock.is_exec, current_sock.data_type)

        # --- PEMBUATAN EDGE BARU ---
        edge = EdgeItem(current_sock, target_sock)
        self.scene().addItem(edge)
        
        # Simpan referensi ke daftar edges di masing-masing socket
        current_sock.edges.append(edge)
        target_sock.edges.append(edge)

        if self.parent_node:
            self.parent_node._recalculate_layout()
        
        if target_sock.parent_node:
            target_sock.parent_node._recalculate_layout()
        
        return edge

    def clear_connections(self):
        """Menghapus kabel yang menempel pada satu socket tertentu"""
        for edge in self.edges[:]:
            self.remove_connections(edge)
    
    def remove_connections(self, edge):
        """Menghapus referensi edge tertentu dari socket ini"""
        if edge in self.edges:
            # Cari socket di ujung satunya agar kita bisa hapus referensi di sana juga
            other_sock = edge.start_socket if edge.end_socket == self else edge.end_socket
            if other_sock and edge in other_sock.edges:
                other_sock.edges.remove(edge)
            
            # Hapus dari socket ini
            self.edges.remove(edge)
            
            # Hapus visual dari scene
            if edge.scene():
                self.scene().removeItem(edge)
        
        if self.parent_node:
            self.parent_node._recalculate_layout()

    def destroy(self):
        # Hapus semua edge yang terhubung
        for edge in self.edges[:]:
            edge = cast('EdgeItem', edge)
            if edge in edge.start_socket.edges:
                edge.start_socket.edges.remove(edge)
                if edge.start_socket.parent_node:
                    edge.start_socket.parent_node._recalculate_layout()
            if edge in edge.end_socket.edges:
                edge.end_socket.edges.remove(edge)
                if edge.end_socket.parent_node:
                        edge.end_socket.parent_node._recalculate_layout()
            if edge.scene():
                edge.scene().removeItem(edge)
        
        # Hapus referensi node induk
        if self.parent_node:
            self.parent_node.inputs = [s for s in self.parent_node.inputs if s != self]
            self.parent_node.outputs = [s for s in self.parent_node.outputs if s != self]

            self.parent_node = None
        
        self.edges.clear()
        
        # Hapus socket dari scene jika masih ada
        if self.scene() is not None:
            self.scene().removeItem(self)
    
    def serialize(self):
        return {
            "id": id(self),
            "is_input": self.is_input,
            "is_exec": self.is_exec,
            "data_type": self.data_type,
            "label": self.label,
            "connections": [
                {
                    "other_node_id": edge.end_socket.parent_node.id if edge.start_socket == self else edge.start_socket.parent_node.id,
                    "other_socket_index": edge.end_socket.index if edge.start_socket == self else edge.start_socket.index
                }
                for edge in self.edges
            ]
        }