from __future__ import annotations
from enum import Enum
from typing import TYPE_CHECKING, cast

from PyQt6.QtWidgets import (QGraphicsItem, QGraphicsView, QMenu, QToolButton)
from PyQt6.QtCore import Qt, QEvent, QSize, QPoint, QPointF
from PyQt6.QtGui import QKeyEvent, QPainter, QMouseEvent, QIcon, QContextMenuEvent, QAction, QResizeEvent, QWheelEvent, QNativeGestureEvent

from Core.Graph.BaseNode import BaseNode
from Core.Graph.EdgeItem import EdgeItem
from Core.Graph.NodeRegistry import NODE_REGISTRY
from Core.Graph.SocketItem import SocketItem

from Core.Nodes.RerouteNode import RerouteNode
from Core.View.GraphScene import GraphScene

if TYPE_CHECKING:
    from Main import MainWindow

class ContextMenuMode(Enum):
    VIEW = 1
    EDGE_DROP = 2

class GraphView(QGraphicsView):
    def __init__(self, scene: GraphScene, main_window: MainWindow):
        super().__init__(scene)
        self.main_window = main_window
        self.setRenderHints(
            QPainter.RenderHint.Antialiasing
            | QPainter.RenderHint.SmoothPixmapTransform
        )
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        # Sembunyikan Scrollbar agar terlihat lebih clean (opsional)
        # self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        # self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Pengaturan Zoom
        self.zoom_factor = 1.15
        self.zoom_level = 0
        self.zoom_range = [-10, 10] # Membatasi seberapa jauh bisa zoom in/out

        # Tombol Zoom In / Zoom Out
        self.zoom_in_btn = QToolButton(self)
        self.zoom_in_btn.setIcon(QIcon("resources/zoom_in.png"))
        self.zoom_in_btn.setIconSize(QSize(32, 32))
        self.zoom_in_btn.setToolTip("Zoom In")
        self.zoom_in_btn.clicked.connect(self.zoom_in) # type: ignore

        self.zoom_out_btn = QToolButton(self)
        self.zoom_out_btn.setIcon(QIcon("resources/zoom_out.png"))
        self.zoom_out_btn.setIconSize(QSize(32, 32))
        self.zoom_out_btn.setToolTip("Zoom Out")
        self.zoom_out_btn.clicked.connect(self.zoom_out) # type: ignore

        # Optional: style biar kelihatan overlay
        self.zoom_in_btn.setAutoRaise(True)
        self.zoom_out_btn.setAutoRaise(True)

        # Custom context menu
        self._right_button_pressed = False
        self._dragging = False
        self._press_pos = QPoint()
        self._last_pos = QPoint()
        self._drag_threshold = 5

        self._update_button_positions()
    
    # ===== Floating Layout =====
    #region Floating Layout
    
    def zoom_in(self):
        if self.zoom_level < self.zoom_range[1]:
            self.scale(self.zoom_factor, self.zoom_factor)
            self.zoom_level += 1

    def zoom_out(self):
        if self.zoom_level > self.zoom_range[0]:
            self.scale(1 / self.zoom_factor, 1 / self.zoom_factor)
            self.zoom_level -= 1

    #endregion Floating Layout
    
    # ===== Input Event =====
    #region Input Events
    
    def keyPressEvent(self, event: QKeyEvent | None):
        if event is None:
            return

        # Deteksi tombol Delete atau Backspace
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Back):
            self._delete_selected_nodes()
        else:
            super().keyPressEvent(event)
        
    def mousePressEvent(self, event: QMouseEvent | None):
        if event is None:
            return

        # Deteksi Tombol Kanan Mouse (Panning)
        if event.button() == Qt.MouseButton.RightButton:
            self._right_button_pressed = True
            self._dragging = False
            self._press_pos = event.pos()
            self._last_pos = event.pos()
            event.accept()
            return
        
        else:
            # Perilaku standar untuk tombol kiri/kanan (koneksi, seleksi, dsb)
            item = self.itemAt(event.pos())
            scene = self.scene()
            if scene is None:
                super().mousePressEvent(event)
                return
            scene = cast(GraphScene, scene)

            if isinstance(item, SocketItem):
                if not item.is_input:
                    scene.start_socket = item
                    scene.temp_edge = EdgeItem(item, None, self.mapToScene(event.pos()))
                    scene.addItem(scene.temp_edge)
                    return 
            
            super().mousePressEvent(event)
            
            # Update Properties Panel
            sel_items = scene.selectedItems()
            if sel_items and isinstance(sel_items[0], BaseNode):
                self.main_window.properties_panel.load_node(sel_items[0])
            else:
                self.main_window.properties_panel.load_node(None)
                self.main_window.properties_panel.clear()
    
    def mouseDoubleClickEvent(self, event: QMouseEvent | None):
        if event is None:
            return

        item = self.itemAt(event.pos())

        # Cari parent node
        node_item = item
        while node_item and not isinstance(node_item, BaseNode):
            node_item = node_item.parentItem()

        # === NODE ===
        if isinstance(node_item, BaseNode):
            self.resetTransform()
            self.zoom_level = 0
            self.centerOn(node_item)
            return

        # === EDGE ===
        if isinstance(item, EdgeItem):
            self._create_reroute_on_edge(item, self.mapToScene(event.pos()))
            return

        # Default behavior
        super().mouseDoubleClickEvent(event)
        

    def mouseMoveEvent(self, event: QMouseEvent | None):
        if event is None:
            return
    
        scene = self.scene()
        if scene is None:
            super().mouseMoveEvent(event)
            return
        scene = cast(GraphScene, scene)

        # === PRIORITAS 1: Drag edge ===
        if scene.temp_edge:
            scene.temp_edge.cur_mouse_pos = self.mapToScene(event.pos())
            scene.temp_edge.update_path()
            return

        # === PRIORITAS 2: Right-click panning ===
        if self._right_button_pressed:
            delta_from_press = event.pos() - self._press_pos

            if not self._dragging and delta_from_press.manhattanLength() > self._drag_threshold:
                self._dragging = True
                self.setCursor(Qt.CursorShape.ClosedHandCursor)

            if self._dragging:
                delta = event.pos() - self._last_pos
                self._last_pos = event.pos()

                hbar = self.horizontalScrollBar()
                if hbar is not None:
                    hbar.setValue(hbar.value() - delta.x())

                vbar = self.verticalScrollBar()
                if vbar is not None:
                    vbar.setValue(vbar.value() - delta.y())

                event.accept()
                return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent | None):
        if event is None:
            super().mouseReleaseEvent(event)
            return

        if event.button() == Qt.MouseButton.RightButton:
            self.setCursor(Qt.CursorShape.ArrowCursor)

            # Klik kanan diam → context menu
            if not self._dragging:
                self.contextMenuEvent(
                    QContextMenuEvent(
                        QContextMenuEvent.Reason.Mouse,
                        event.pos(),
                        event.globalPosition().toPoint()
                    )
                )

            self._right_button_pressed = False
            self._dragging = False
            event.accept()
            return
        
        scene = self.scene()
        if scene is None:
            super().mouseReleaseEvent(event)
            return
        scene = cast(GraphScene, scene)

        if scene.temp_edge:
            # Sembunyikan sebentar untuk mendeteksi apa yang ada di bawahnya
            scene.temp_edge.hide()
            item = self.itemAt(event.pos())
            out_sock = scene.start_socket
            
            # 1. Jika dilepas di atas socket (Koneksi Langsung)
            if isinstance(item, SocketItem):
                if out_sock is not None and self._is_connection_allowed(out_sock, item):
                    if out_sock.is_input: item.connect_to(out_sock)
                    else: out_sock.connect_to(item)
                
                # Hapus kabel sementara karena sudah jadi kabel permanen
                scene.removeItem(scene.temp_edge)
                scene.temp_edge = None
                scene.start_socket = None

            # 2. Jika dilepas di area kosong (Tampilkan Menu dulu baru hapus)
            else:
                # Tampilkan kembali kabel sementara agar terlihat saat menu terbuka
                scene.temp_edge.show()
                pos_in_scene = self.mapToScene(event.pos())
                
                # PENTING: Menu dipanggil di sini, kabel masih terlihat
                self._show_context_menu(
                    event.globalPosition().toPoint(),
                    pos_in_scene,
                    item=item,
                    mode=ContextMenuMode.EDGE_DROP
                )
                
                # Setelah menu selesai (dipilih atau dicancel), baru hapus kabel sementara
                if scene.temp_edge:
                    scene.removeItem(scene.temp_edge)
                    scene.temp_edge = None
                    scene.start_socket = None
            
        super().mouseReleaseEvent(event)
    
    def wheelEvent(self, event: QWheelEvent | None):
        """Menangani Zoom In / Zoom Out dengan Scroll Mouse"""
        if event is None:
            super().wheelEvent(event)
            return

        angle = event.angleDelta()

        # === TRACKPAD (2-finger scroll → PAN) ===
        is_trackpad = (
            abs(angle.y()) < 120 or 
            abs(angle.x()) > 0 or
            event.phase() != Qt.ScrollPhase.NoScrollPhase
        )

        if is_trackpad:
            # PAN
            hbar = self.horizontalScrollBar()
            vbar = self.verticalScrollBar()
            if hbar is not None:
                hbar.setValue(hbar.value() - angle.x())
            if vbar is not None:
                vbar.setValue(vbar.value() - angle.y())
            return

        # === MOUSE WHEEL → ZOOM ===
        delta = angle.y()

        if delta > 0:
            if self.zoom_level < self.zoom_range[1]:
                self.scale(self.zoom_factor, self.zoom_factor)
                self.zoom_level += 1
        else:
            if self.zoom_level > self.zoom_range[0]:
                self.scale(1 / self.zoom_factor, 1 / self.zoom_factor)
                self.zoom_level -= 1
    
    def event(self, event: QEvent | None):
        if event is None:
            return super().event(event)

        if event.type() == QEvent.Type.NativeGesture:
            gesture_event = cast(QNativeGestureEvent, event)
            if gesture_event.gestureType() == Qt.NativeGestureType.ZoomNativeGesture:
                factor = 1 + gesture_event.value()

                if factor > 1 and self.zoom_level < self.zoom_range[1]:
                    self.scale(factor, factor)
                    self.zoom_level += 1
                elif factor < 1 and self.zoom_level > self.zoom_range[0]:
                    self.scale(factor, factor)
                    self.zoom_level -= 1

                return True
        return super().event(event)

    #endregion Input Events
    
    # ===== Other Event =====
    #region Other Events

    def resizeEvent(self, event: QResizeEvent | None):
        if event is None:
            super().resizeEvent(event)
            return

        super().resizeEvent(event)
        self._update_button_positions()

    def contextMenuEvent(self, event: QContextMenuEvent | None):
        if event is None:
            return

        pos = self.mapToScene(event.pos())
        item = self.itemAt(event.pos())

        if isinstance(item, BaseNode):
            menu = QMenu()

            # Change selected to `item`
            item.setSelected(True)

            act_focus = menu.addAction("Focus This Node") # type: ignore
            act_del = menu.addAction("Delete Node") # type: ignore
            if act_del:
                act_del.setEnabled(item.is_removable)

            selected_menu = menu.exec(event.globalPos()) # type: ignore

            if selected_menu == act_focus:
                self.resetTransform()
                self.zoom_level = 0
                self.centerOn(item)
            
            elif selected_menu == act_del:
                self._delete_selected_nodes()

            return

        self._show_context_menu(
            event.globalPos(),
            pos,
            item=item,
            mode=ContextMenuMode.VIEW
        )
        
        # Refresh Properties Panel
        scene = self.scene()
        if scene:
            sel_items = scene.selectedItems()
            if sel_items and isinstance(sel_items[0], BaseNode):
                self.main_window.properties_panel.load_node(sel_items[0])
            else:
                self.main_window.properties_panel.clear()
        else:
            self.main_window.properties_panel.clear()
    
    #endregion Other Events
        
    # ===== Helpers =====
    #region Helpers

    def _update_button_positions(self):
        margin = 10
        btn_size = self.zoom_in_btn.sizeHint()

        self.zoom_in_btn.move(
            self.width() - btn_size.width() - margin,
            margin
        )

        self.zoom_out_btn.move(
            self.width() - btn_size.width() - margin,
            margin + btn_size.height() + 5
        )

    def _delete_selected_nodes(self):
        scene = self.scene()
        if scene is None:
            return

        for item in scene.selectedItems():
            if isinstance(item, BaseNode) and item.is_removable:
                item.destroy()

                # Bersihkan panel properti jika node yang dihapus sedang ditampilkan
                self.main_window.properties_panel.clear()
    
    def _show_context_menu(
        self,
        global_pos: QPoint,
        scene_pos: QPointF,
        item: QGraphicsItem | None = None,
        mode: ContextMenuMode = ContextMenuMode.VIEW
    ):

        scene = self.scene()

        if scene is None:
            return

        scene = cast(GraphScene, scene)

        def _auto_connect_node(node: BaseNode):

            start_sock = scene.start_socket

            if not start_sock:
                return

            target_sockets = (
                node.inputs
                if not start_sock.is_input
                else node.outputs
            )

            for target_sock in target_sockets:

                if self._is_connection_allowed(
                    start_sock,
                    target_sock
                ):

                    if start_sock.is_input:
                        target_sock.connect_to(start_sock)
                    else:
                        start_sock.connect_to(target_sock)

                    break

        (
            menu,
            node_actions,
            act_focus,
            act_zoom_in,
            act_zoom_out,
            act_select_all
        ) = self._get_context_menu(mode)

        selected_action = menu.exec(global_pos) # type: ignore

        if selected_action is None:
            return

        # =========================================================
        # NODE CREATION
        # =========================================================

        if selected_action in node_actions:

            node_cls = node_actions[selected_action]

            try:
                node = node_cls()

            except Exception as e:
                print(f"Gagal membuat node: {e}")
                return

            node = self.spawn_node(node, scene_pos)

            # EDGE DROP MODE
            if mode == ContextMenuMode.EDGE_DROP:
                _auto_connect_node(node)

            return

        # =========================================================
        # VIEW ACTIONS
        # =========================================================

        if selected_action == act_focus:

            self.resetTransform()
            self.zoom_level = 0
            self.centerOn(scene_pos)

        elif selected_action == act_zoom_in:

            self.zoom_in()

        elif selected_action == act_zoom_out:

            self.zoom_out()

        # =========================================================
        # SELECTION
        # =========================================================

        elif selected_action == act_select_all:

            for item in scene.items():

                if isinstance(item, BaseNode):
                    item.setSelected(True)
    
    def _is_connection_allowed(self, out_sock: SocketItem, in_sock: SocketItem):
        # Dasar: Harus beda (Input vs Output) dan Beda Node
        if out_sock.is_input == in_sock.is_input: return False
        if out_sock.parent_node == in_sock.parent_node: return False
        
        # Strict Typing: Exec hanya ke Exec, Data hanya ke Data yang tipenya sama
        if out_sock.is_exec != in_sock.is_exec:
            return False
        if (out_sock.is_exec == in_sock.is_exec == False) and (out_sock.data_type != in_sock.data_type):
            return False
            
        return True
    
    def _get_context_menu(
        self,
        mode: ContextMenuMode = ContextMenuMode.VIEW
    ) -> tuple[QMenu, dict[QAction, type[BaseNode]], QAction | None, QAction | None, QAction | None, QAction | None]:

        def _add_title(menu: QMenu, title: str):

            title_action = QAction(title, self)

            font = title_action.font()
            font.setBold(True)

            title_action.setFont(font)
            title_action.setEnabled(False)

            menu.addAction(title_action) # type: ignore
            menu.addSeparator()

        menu = QMenu()

        node_actions: dict[QAction, type[BaseNode]] = {}

        # =========================================================
        # ADD NODE
        # =========================================================

        _add_title(menu, "Add Node")

        category_menus: dict[str, QMenu] = {}

        for _, node_cls in sorted(
            NODE_REGISTRY.items(),
            key=lambda x: x[0]
        ):
            category = getattr(node_cls, "CATEGORY", None)

            # HIDDEN
            if category == "HIDDEN":
                continue

            action = QAction(node_cls.NODE_NAME, self)
            action.setData(node_cls)

            node_actions[action] = node_cls

            # ROOT CATEGORY
            if not category:
                menu.addAction(action) # type: ignore
                continue

            # =========================
            # NESTED CATEGORY SUPPORT
            # =========================
            parts = category.split("/")

            parent_menu = menu
            path_key = ""

            for part in parts:
                path_key = f"{path_key}/{part}" if path_key else part

                if path_key not in category_menus:
                    sub_menu = cast(QMenu, parent_menu.addMenu(part))
                    if sub_menu:
                        category_menus[path_key] = sub_menu

                parent_menu = category_menus[path_key]

            parent_menu.addAction(action) # type: ignore

        # =========================================================
        # VIEW
        # =========================================================

        menu.addSeparator()

        _add_title(menu, "View")

        act_focus = menu.addAction("Focus Here") # type: ignore
        act_zoom_in = menu.addAction("Zoom In") # type: ignore
        act_zoom_out = menu.addAction("Zoom Out") # type: ignore

        if mode != ContextMenuMode.VIEW:

            for act in (
                act_focus,
                act_zoom_in,
                act_zoom_out
            ):
                if act:
                    act.setVisible(False)

        # =========================================================
        # SELECTION
        # =========================================================

        menu.addSeparator()

        _add_title(menu, "Selection")

        act_select_all = menu.addAction("Select All") # type: ignore

        if mode != ContextMenuMode.VIEW:
            if act_select_all:
                act_select_all.setVisible(False)

        return (
            menu,
            node_actions,
            act_focus,
            act_zoom_in,
            act_zoom_out,
            act_select_all
        )
    
    def spawn_node(self, node: BaseNode, pos: QPointF):
        """Helper untuk menaruh node di scene dan menampilkannya"""
        node.setPos(pos)

        scene = self.scene()
        if scene is not None:
            scene.addItem(node)
            scene.clearSelection()
        node.setSelected(True)
        self.main_window.properties_panel.load_node(node)
        return node

    def _create_reroute_on_edge(self, edge: EdgeItem, pos: QPointF):
        """Menyisipkan reroute node di tengah kabel"""
        start_socket = edge.start_socket
        end_socket = edge.end_socket
        s_exec = start_socket.is_exec
        s_type = start_socket.data_type

        # 1. Buat Reroute Node baru
        reroute = RerouteNode(is_exec=s_exec, socket_data_type=s_type)
        reroute.setPos(pos.x() - 10, pos.y() - 10)

        scene = self.scene()
        if scene is not None:
            scene.addItem(reroute)

        # 2. Hapus kabel lama
        if scene is not None:
            scene.removeItem(edge)
        start_socket.edges.remove(edge)

        if end_socket:
            end_socket.edges.remove(edge)

        # 3. Buat dua kabel baru (Sambungkan Start -> Reroute -> End)
        start_socket.connect_to(reroute.in_socket)
        if end_socket:
            reroute.out_socket.connect_to(end_socket)
    
    #endregion Helpers