from __future__ import annotations
from typing import TYPE_CHECKING

from PyQt6.QtWidgets import (QGraphicsScene)
from PyQt6.QtCore import QObject, QPointF, QRectF
from PyQt6.QtGui import QPainter, QPen

from Style import STYLES

if TYPE_CHECKING:
    from Core.Graph.SocketItem import SocketItem
    from Core.Graph.EdgeItem import EdgeItem

class GraphScene(QGraphicsScene):
    def __init__(self, parent: QObject|None =None):
        super().__init__(parent)
        self.setSceneRect(0, 0, 5000, 5000)
        self.setBackgroundBrush(STYLES['bg_color'])
        
        # State Dragging Connection
        self.temp_edge: EdgeItem | None = None
        self.start_socket: SocketItem | None = None

    def drawBackground(self, painter: QPainter | None, rect: QRectF):
        super().drawBackground(painter, rect)
        # Simple Grid
        grid_size = 20
        left = int(rect.left()) - (int(rect.left()) % grid_size)
        top = int(rect.top()) - (int(rect.top()) % grid_size)
        
        lines: list[tuple[QPointF, QPointF]] = []
        axis_lines: list[tuple[QPointF, QPointF]] = []
        
        # Vertical lines
        x = left
        while x < rect.right():
            line = (QPointF(x, rect.top()), QPointF(x, rect.bottom()))
            if x == int(self.sceneRect().width() / 2):
                axis_lines.append(line)
            else:
                lines.append(line)
            x += grid_size
        
        # Horizontal lines
        y = top
        while y < rect.bottom():
            line = (QPointF(rect.left(), y), QPointF(rect.right(), y))
            if y == int(self.sceneRect().height() / 2):
                axis_lines.append(line)
            else:
                lines.append(line)
            y += grid_size

        if painter is None:
            return

        # Draw grid lines
        painter.setPen(QPen(STYLES['grid_color'], 1))
        for p1, p2 in lines:
            painter.drawLine(p1, p2)
        
        # Draw axes with thicker pen
        painter.setPen(QPen(STYLES['grid_color'], 2))
        for p1, p2 in axis_lines:
            painter.drawLine(p1, p2)