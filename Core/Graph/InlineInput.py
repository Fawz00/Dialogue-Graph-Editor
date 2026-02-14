import sys
from PyQt6.QtWidgets import (QGraphicsItem, QSizePolicy, QGraphicsProxyWidget, QWidget, QHBoxLayout)
from PyQt6.QtCore import Qt, QRectF, QSize
from PyQt6.QtGui import QPen, QPainterPath, QFont

class InlineInput:
    def __init__(self, node, socket, widget: QWidget):
        self.node = node
        self.socket = socket

        self.proxy = QGraphicsProxyWidget(node)
        self.proxy.setWidget(widget)
        self.proxy.setZValue(2)

    def destroy(self):
        if self.proxy.scene():
            self.proxy.scene().removeItem(self.proxy)
        self.proxy.setWidget(None)
        self.proxy = None

    def set_visible(self, visible: bool):
        if self.proxy:
            self.proxy.setVisible(visible)

    def size(self):
        return self.proxy.size() if self.proxy else QSize(0, 0)
