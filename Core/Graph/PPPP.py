import sys
from PyQt6.QtWidgets import (QGraphicsItem, QSizePolicy, QGraphicsProxyWidget, QWidget, QHBoxLayout)
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPen, QPainterPath, QFont
from typing import cast

from Core.Enums.DataType import DataType
from Core.UIPanel.Utils.PropertyWidgetFactory import PropertyWidgetFactory
from Style import STYLES
from Core.Graph.SocketItem import SocketItem
from Core.Graph.InlineInput import InlineInput
from Core.Debug import Debug
from Core.VariableManager import VariableManager
from Core.Structures.Variable import Variable

class BaseNode(QGraphicsItem):
    main_window = None

    def __init__(self, title="Node"):
        super().__init__()
        self.title = title
        self.is_removable = True
        self.is_valid = True
        self.properties = dict[str, Variable]() # key: property name, value: Variable instance
        self.content_width = 120
        self.width = 150
        self.height = 80
        self.socket_spacing = 25 # default: 25, 40 better for inline

        # Exec Sockets
        self.exec_inputs: list[SocketItem] = []
        self.exec_outputs: list[SocketItem] = []

        # Data Sockets
        self.data_inputs: list[SocketItem] = []
        self.data_outputs: list[SocketItem] = []

        # Flags
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        
        # Header Color (bisa di override per tipe node)
        self.header_color = STYLES['node_header']

    # ========== Qt Overrides ==========
    #region Qt Overrides

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
        painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        painter.drawText(QRectF(10, 0, self.width-20, 30), Qt.AlignmentFlag.AlignVCenter, self.title)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            # Update edges connected to this node
            for sock in self.data_inputs + self.data_outputs:
                for edge in sock.edges:
                    edge.update_path()
        return super().itemChange(change, value)
    
    #endregion Qt Overrides



    # ========== Node Methods ==========
    # region Socket Management

    def add_exec_socket(self, is_input, label=""):
        socket = SocketItem(self, len(self.exec_inputs) if is_input else len(self.exec_outputs), is_input, is_exec=True, data_type=None, label=label, prop_reference_path=[])
        if is_input:
            self.exec_inputs.append(socket)
        else:
            self.exec_outputs.append(socket)
        self._update_socket_positions()
        return socket
    
    def add_data_socket(self, is_input, data_type: DataType =None, label="", prop_reference_path=[]):
        socket = SocketItem(self, len(self.data_inputs) if is_input else len(self.data_outputs), is_input, is_exec=False, data_type=data_type, label=label, prop_reference_path=prop_reference_path)
        if is_input:
            self.data_inputs.append(socket)
        else:
            self.data_outputs.append(socket)
        self._update_socket_positions()
        return socket

    def change_data_socket(self, socket: SocketItem, data_type=None, label="", prop_reference_path=[]):
        """Mengganti properti socket tanpa menghapusnya"""
        if socket not in self.data_inputs and socket not in self.data_outputs:
            Debug.log_error("Socket not found in this node.")
            return

        socket.change_type(is_exec=False, data_type=data_type, label=label)
        socket.change_var_ref(prop_reference_path)
        self._update_socket_positions()
        return socket
    
    def change_exec_socket(self, socket: SocketItem, label=""):
        """Mengganti properti socket tanpa menghapusnya"""
        if socket not in self.exec_inputs and socket not in self.exec_outputs:
            Debug.log_error("Socket not found in this node.")
            return

        socket.change_type(is_exec=True, data_type=None, label=label)
        self._update_socket_positions()
        return socket

    def remove_socket(self, socket):
        """Menghapus socket secara bersih dari list dan scene"""
        if socket in self.data_inputs:
            self.data_inputs.remove(socket)
        if socket in self.data_outputs:
            self.data_outputs.remove(socket)
        socket.destroy()
        
        self._update_socket_positions()
    
    def clear_data_sockets(self):
        """Menghapus semua socket dari node"""
        for sock in self.data_inputs + self.data_outputs:
            sock.destroy()
        
        self.data_inputs = []
        self.data_outputs = []
        self._update_socket_positions()
    
    def clear_exec_sockets(self):
        """Menghapus semua socket dari node"""
        for sock in self.exec_inputs + self.exec_outputs:
            sock.destroy()
        
        self.exec_inputs = []
        self.exec_outputs = []
        self._update_socket_positions()
    
    def validate_socket_connections(self):
        """Memutus kabel jika tipe data socket berubah dan tidak cocok dengan kabelnya"""
        for socket in self.data_inputs + self.data_outputs + self.exec_inputs + self.exec_outputs:
            if socket.is_exec:
                continue # Lewati alur eksekusi
            
            for edge in socket.edges[:]:
                # Ambil socket lawan
                other_socket = edge.start_socket if edge.end_socket == socket else edge.end_socket
                other_socket = cast(SocketItem, other_socket)
                
                # Jika tipe data sudah tidak sama, putus koneksinya!
                if socket.data_type != other_socket.data_type:
                    self.remove_socket(socket)

    def _update_socket_positions(self):
        # Hitung tinggi node berdasarkan jumlah socket
        count_in = len(self.data_inputs) + len(self.exec_inputs)
        count_out = len(self.data_outputs) + len(self.exec_outputs)
        max_sockets = max(count_in, count_out)
        
        self.height = max(self.height, 40 + (max_sockets * self.socket_spacing))
        
        y_start = 45
        for i, sock in enumerate(self.data_inputs):
            sock.setPos(0, y_start + (i * self.socket_spacing))
        for i, sock in enumerate(self.exec_inputs):
            sock.setPos(0, y_start + ((len(self.data_inputs) + i) * self.socket_spacing))
            
        for i, sock in enumerate(self.data_outputs):
            sock.setPos(self.width, y_start + (i * self.socket_spacing))
        for i, sock in enumerate(self.exec_outputs):
            sock.setPos(self.width, y_start + ((len(self.data_outputs) + i) * self.socket_spacing))
            
        self.update() # Redraw

    #endregion Socket Management

    def add_inline_input(self, socket: SocketItem, prop_reference_path: list[str]):
        prop_var = None
        for prop_name in prop_reference_path:
            if prop_var is None:
                prop_var = self.properties.get(prop_name)
            else:
                # Jika properti sebelumnya adalah Variable yang berisi dict, lanjutkan ke level berikutnya
                if isinstance(prop_var.value, dict):
                    prop_var = prop_var.value.get(prop_name)
                else:
                    Debug.log_error(f"Property path '{prop_reference_path}' is invalid at '{prop_name}'")
                    return

        if not prop_var:
            Debug.log_error(f"Property '{prop_reference_path}' not found")
            return

        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        editor = PropertyWidgetFactory.create(
            layout,
            prop_reference_path[-1],
            prop_var,
            lambda v, k=prop_reference_path: self.set_property(v, k),
            prop_reference_path
        )

        editor.setMinimumWidth(60)
        editor.setMaximumWidth(160)
        editor.setStyleSheet(
            "background:#111; color:white; border:1px solid #444;"
        )

        self.change_data_socket(socket, data_type=prop_var.type, label=prop_reference_path[-1], prop_reference_path=prop_reference_path)

        self._recalculate_layout()
    
    def _recalculate_layout(self):
        # self.prepareGeometryChange()
        self._update_socket_positions()
        self.update()
    
    def destroy(self):
        # Hapus semua socket
        self.clear_data_sockets()
        self.clear_exec_sockets()
        # Hapus node dari scene
        if self.scene() is not None:
            self.scene().removeItem(self)

    def refresh(self):
        """Override ini untuk memperbarui tampilan atau data internal node"""
        pass

    def get_properties(self) -> dict:
        """Override ini untuk menampilkan properti di panel samping"""
        return {}

    def set_property(self, key_path: list, value):
        """Override ini untuk menerima update properti"""
        VariableManager.edit_variable(
            database=self.properties,
            value_path=key_path,
            new_data=Variable(
                type=None,
                value=value
            )
        )

        if main_window := BaseNode.main_window:
            main_window.properties_panel.refresh()

    def serialize(self):
        """Mengubah node menjadi dict untuk disimpan"""
        return {
            "id": id(self),
            "title": self.title,
            "pos": (self.pos().x(), self.pos().y()),
            "node_type": self.__class__.__name__,
            "properties": self.properties,
            "data_sockets": {
                "inputs": [sock.serialize() for sock in self.data_inputs],
                "outputs": [sock.serialize() for sock in self.data_outputs]
            },
            "exec_sockets": {
                "inputs": [sock.serialize() for sock in self.exec_inputs],
                "outputs": [sock.serialize() for sock in self.exec_outputs]
            }
        }

    def execute(self) -> SocketItem:
        """Override ini untuk menjalankan logika node saat dieksekusi"""
        return self.outputs[0] if self.outputs else None # Default: langsung ke output pertama (jika ada)
    
    #endregion Node Methods
