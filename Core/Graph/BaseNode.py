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
        self.properties = {}
        self.content_width = 120
        self.width = 150
        self.height = 80
        self.socket_spacing = 25 # default: 25, 40 better for inline

        # Sockets
        self.inputs = []
        self.outputs = []

        # Inline Inputs and Proxy Widgets
        self.inline_inputs = {}

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
        painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        painter.drawText(QRectF(10, 0, self.width-20, 30), Qt.AlignmentFlag.AlignVCenter, self.title)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            # Update edges connected to this node
            for sock in self.inputs + self.outputs:
                for edge in sock.edges:
                    edge.update_path()
        return super().itemChange(change, value)
    
    #endregion Qt Overrides

    # ========== Node Methods ==========
    #region Node Methods

    # region Socket Management

    def add_socket(self, is_input, is_exec=True, data_type: DataType =None, label=""):
        socket = SocketItem(self, len(self.inputs) if is_input else len(self.outputs), is_input, is_exec=is_exec, data_type=data_type, label=label)
        if is_input:
            self.inputs.append(socket)
        else:
            self.outputs.append(socket)
        self._update_socket_positions()
        return socket

    def change_socket(self, socket, is_exec=True, data_type=None, label=""):
        """Mengganti properti socket tanpa menghapusnya"""
        socket.change_type(is_exec=is_exec, data_type=data_type, label=label)
        self._update_socket_positions()
        return socket

    def remove_socket(self, socket):
        """Menghapus socket secara bersih dari list dan scene"""
        if socket in self.inputs:
            self.inputs.remove(socket)
        if socket in self.outputs:
            self.outputs.remove(socket)
        if socket in self.inline_inputs:
            self.inline_inputs[socket].destroy()
            del self.inline_inputs[socket]
        socket.destroy()
        
        self._update_socket_positions()
    
    def clear_sockets(self):
        """Menghapus semua socket dari node"""
        for sock in self.inputs + self.outputs:
            sock.destroy()
        
        self.inputs = []
        self.outputs = []
        self._update_socket_positions()
    
    def validate_socket_connections(self):
        """Memutus kabel jika tipe data socket berubah dan tidak cocok dengan kabelnya"""
        for socket in self.inputs + self.outputs:
            socket = cast(SocketItem, socket)
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
        count_in = len(self.inputs)
        count_out = len(self.outputs)
        max_sockets = max(count_in, count_out)
        
        self.height = max(self.height, 40 + (max_sockets * self.socket_spacing))
        
        y_start = 45
        for i, sock in enumerate(self.inputs):
            sock.setPos(0, y_start + (i * self.socket_spacing))
            
        for i, sock in enumerate(self.outputs):
            sock.setPos(self.width, y_start + (i * self.socket_spacing))
            
        self.update() # Redraw
    
    #endregion Socket Management

    def add_inline_input(self, socket, prop_var_name: str):
        prop_var = self.properties.get(prop_var_name)
        if not prop_var:
            Debug.log_error(f"Property '{prop_var_name}' not found")
            return

        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        editor = PropertyWidgetFactory.create(
            layout,
            prop_var_name,
            prop_var,
            lambda v, k=[prop_var_name]: self.set_property(v, k),
            [prop_var_name]
        )

        editor.setMinimumWidth(60)
        editor.setMaximumWidth(160)
        editor.setStyleSheet(
            "background:#111; color:white; border:1px solid #444;"
        )

        inline = InlineInput(self, socket, container)
        self.inline_inputs[socket] = inline

        self._recalculate_layout()
    
    def _recalculate_layout(self):
        extra_width = 0

        for sock, inline in self.inline_inputs.items():
            if sock.is_input and len(sock.edges) == 0:
                extra_width = max(extra_width, inline.size().width())

        self.prepareGeometryChange()
        self.width = int(self.content_width + extra_width + 20)
        self._update_socket_positions()
        self.update_inline_positions()
        self.update()
    
    def update_inline_positions(self):
        for sock, inline in self.inline_inputs.items():
            visible = sock.is_input and len(sock.edges) == 0
            inline.set_visible(visible)

            if not visible:
                continue

            try:
                index = self.inputs.index(sock)
            except ValueError:
                # Socket might already be removed/deleted from inputs
                inline.set_visible(False)
                continue
            y = 45 + index * self.socket_spacing - 12
            x = 18  # kanan socket

            inline.proxy.setPos(x, y)
    
    def destroy(self):
        # Hapus semua socket
        self.clear_sockets()
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
            "sockets": {
                "inputs": [sock.serialize() for sock in self.inputs],
                "outputs": [sock.serialize() for sock in self.outputs]
            }
        }
    
    #endregion Node Methods
