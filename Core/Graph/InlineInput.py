from __future__ import annotations
from typing import TYPE_CHECKING

from PyQt6.QtWidgets import (QGraphicsProxyWidget, QWidget)
from PyQt6.QtCore import QSize

if TYPE_CHECKING:
    from Core.Graph.BaseNode import BaseNode
    from Core.Graph.SocketItem import SocketItem

class InlineInput:
    def __init__(self, node: BaseNode, socket: SocketItem, widget: QWidget):
        self.node = node
        self.socket = socket

        self.proxy = QGraphicsProxyWidget(node)
        self.proxy.setWidget(widget)
        self.proxy.setZValue(2)

    def destroy(self):
        proxy = self.proxy
        if proxy is None:
            return

        scene = proxy.scene()
        if scene:
            scene.removeItem(proxy)
        proxy.setWidget(None)
        self.proxy = None

    def set_visible(self, visible: bool):
        if self.proxy:
            self.proxy.setVisible(visible)

    def size(self):
        return self.proxy.size() if self.proxy else QSize(0, 0)
