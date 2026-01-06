import sys
from PyQt6.QtWidgets import (QGraphicsView, QMenu, QToolButton)
from PyQt6.QtCore import Qt, QEvent, QSize
from PyQt6.QtGui import QPainter, QMouseEvent, QIcon

from Core.BaseNode import BaseNode
from Core.Enums.DataType import DataType
from Core.Graph.EdgeItem import EdgeItem
from Core.Graph.SocketItem import SocketItem

from Core.Nodes.DialogueNode import DialogueNode
from Core.Nodes.SetVarNode import SetVarNode
from Core.Nodes.RerouteNode import RerouteNode

class GraphView(QGraphicsView):
    def __init__(self, scene, main_window):
        super().__init__(scene)
        self.main_window = main_window
        self.setRenderHints(
            QPainter.RenderHint.Antialiasing
            | QPainter.RenderHint.SmoothPixmapTransform
        )
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)

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
        self.zoom_in_btn.clicked.connect(self.zoom_in)

        self.zoom_out_btn = QToolButton(self)
        self.zoom_out_btn.setIcon(QIcon("resources/zoom_out.png"))
        self.zoom_out_btn.setIconSize(QSize(32, 32))
        self.zoom_out_btn.setToolTip("Zoom Out")
        self.zoom_out_btn.clicked.connect(self.zoom_out)

        # Optional: style biar kelihatan overlay
        self.zoom_in_btn.setAutoRaise(True)
        self.zoom_out_btn.setAutoRaise(True)

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
    
    def keyPressEvent(self, event):
        # Deteksi tombol Delete atau Backspace
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Back):
            self._delete_selected_nodes()
        else:
            super().keyPressEvent(event)
        
    def mousePressEvent(self, event):
        # Deteksi Tombol Tengah Mouse (Panning)
        if event.button() == Qt.MouseButton.MiddleButton:
            self.middle_mouse_button_press(event)
        else:
            # Perilaku standar untuk tombol kiri/kanan (koneksi, seleksi, dsb)
            item = self.itemAt(event.pos())
            if isinstance(item, SocketItem):
                if not item.is_input:
                    self.scene().start_socket = item
                    self.scene().temp_edge = EdgeItem(item, None, self.mapToScene(event.pos()))
                    self.scene().addItem(self.scene().temp_edge)
                    return 
            
            super().mousePressEvent(event)
            
            # Update Properties Panel
            sel_items = self.scene().selectedItems()
            if sel_items and isinstance(sel_items[0], BaseNode):
                self.main_window.properties_panel.load_node(sel_items[0])
            else:
                self.main_window.properties_panel.load_node(None)
                self.main_window.properties_panel.clear()
    
    def mouseDoubleClickEvent(self, event):
        item = self.itemAt(event.pos())
        
        # Jika double click pada kabel (EdgeItem)
        if isinstance(item, EdgeItem):
            self._create_reroute_on_edge(item, self.mapToScene(event.pos()))
        else:
            super().mouseDoubleClickEvent(event)

    def mouseMoveEvent(self, event):
        if self.scene().temp_edge:
            self.scene().temp_edge.cur_mouse_pos = self.mapToScene(event.pos())
            self.scene().temp_edge.update_path()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton:
            self.middle_mouse_button_release(event)
            return

        if self.scene().temp_edge:
            # Sembunyikan sebentar untuk mendeteksi apa yang ada di bawahnya
            self.scene().temp_edge.hide()
            item = self.itemAt(event.pos())
            out_sock = self.scene().start_socket
            
            # 1. Jika dilepas di atas socket (Koneksi Langsung)
            if isinstance(item, SocketItem):
                if self._is_connection_allowed(out_sock, item):
                    if out_sock.is_input: item.connect_to(out_sock)
                    else: out_sock.connect_to(item)
                
                # Hapus kabel sementara karena sudah jadi kabel permanen
                self.scene().removeItem(self.scene().temp_edge)
                self.scene().temp_edge = None
                self.scene().start_socket = None

            # 2. Jika dilepas di area kosong (Tampilkan Menu dulu baru hapus)
            else:
                # Tampilkan kembali kabel sementara agar terlihat saat menu terbuka
                self.scene().temp_edge.show()
                pos_in_scene = self.mapToScene(event.pos())
                
                # PENTING: Menu dipanggil di sini, kabel masih terlihat
                self._show_context_menu_at_drop(event.globalPosition().toPoint(), pos_in_scene)
                
                # Setelah menu selesai (dipilih atau dicancel), baru hapus kabel sementara
                if self.scene().temp_edge:
                    self.scene().removeItem(self.scene().temp_edge)
                    self.scene().temp_edge = None
                    self.scene().start_socket = None
            
        super().mouseReleaseEvent(event)
    
    def wheelEvent(self, event):
        """Menangani Zoom In / Zoom Out dengan Scroll Mouse"""
        # Tentukan arah scroll
        delta = event.angleDelta().y()
        
        if delta > 0: # Scroll ke atas (Zoom In)
            if self.zoom_level < self.zoom_range[1]:
                self.scale(self.zoom_factor, self.zoom_factor)
                self.zoom_level += 1
        else: # Scroll ke bawah (Zoom Out)
            if self.zoom_level > self.zoom_range[0]:
                self.scale(1 / self.zoom_factor, 1 / self.zoom_factor)
                self.zoom_level -= 1
    
    def middle_mouse_button_press(self, event):
        """Aktifkan mode geser (ScrollHandDrag)"""
        release_event = QMouseEvent(QEvent.Type.MouseButtonRelease, event.position(), 
                                    Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton, 
                                    event.modifiers())
        super().mouseReleaseEvent(release_event)
        
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        
        # Simulasikan klik kiri agar ScrollHandDrag langsung berjalan
        fake_event = QMouseEvent(event.type(), event.position(), 
                                 Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton, 
                                 event.modifiers())
        super().mousePressEvent(fake_event)

    def middle_mouse_button_release(self, event):
        """Kembalikan mode ke seleksi kotak (RubberBandDrag)"""
        fake_event = QMouseEvent(event.type(), event.position(), 
                                 Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton, 
                                 event.modifiers())
        super().mouseReleaseEvent(fake_event)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)

    #endregion Input Events
    
    # ===== Other Event =====
    #region Other Events

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_button_positions()

    def contextMenuEvent(self, event):
        pos = self.mapToScene(event.pos())
        item = self.itemAt(event.pos())
        
        if isinstance(item, BaseNode):
            # Menu hapus untuk node (Logika sudah kita buat sebelumnya)
            menu = QMenu()
            if not item.isSelected():
                self.scene().clearSelection()
                item.setSelected(True)
            
            act_del = menu.addAction("Delete Node")
            if not item.is_removable:
                act_del.setEnabled(False)
            
            action = menu.exec(event.globalPos())
            if action == act_del: self._delete_selected_nodes()
            
        else:
            # Menu tambah node
            menu, act_dial, set_var_menu, act_reroute = self._get_context_menu(pos)
            selected_action = menu.exec(event.globalPos())
            
            if selected_action == act_dial:
                self.spawn_node(DialogueNode(), pos)
            elif selected_action and selected_action.parent() == set_var_menu:
                var_name = selected_action.data()
                node = SetVarNode(self.main_window.var_manager)
                self.spawn_node(node, pos)
                node.set_property(["Variable"], var_name) # Otomatis set variabelnya
            elif selected_action == act_reroute:
                reroute = RerouteNode()
                self.spawn_node(reroute, pos)
        
        # Refresh Properties Panel
        sel_items = self.scene().selectedItems()
        if sel_items and isinstance(sel_items[0], BaseNode):
            self.main_window.properties_panel.load_node(sel_items[0])
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
        for item in self.scene().selectedItems():
            if isinstance(item, BaseNode) and item.is_removable:
                item.destroy()

                # Bersihkan panel properti jika node yang dihapus sedang ditampilkan
                self.main_window.properties_panel.clear()
    
    def _show_context_menu_at_drop(self, global_pos, scene_pos):
        """Dipanggil saat kabel dilepas di area kosong"""
        menu, act_dial, set_var_menu, act_reroute = self._get_context_menu(scene_pos)
        
        # Eksekusi menu secara synchronous
        selected_action = menu.exec(global_pos)
        
        new_node = None
        if selected_action == act_dial:
            new_node = DialogueNode()
        elif selected_action and selected_action.parent() == set_var_menu:
            var_name = selected_action.data()
            new_node = SetVarNode(self.main_window.var_manager)
            new_node.set_property(["Variable"], var_name)
        elif selected_action == act_reroute:
            start_sock = self.scene().start_socket
            new_node = RerouteNode(start_sock.is_exec, start_sock.data_type) if hasattr(start_sock.parent_node, 'is_reroute') else RerouteNode()
            self.spawn_node(new_node, scene_pos)
            
            # Hubungkan otomatis
            if start_sock.is_input:
                new_node.out_socket.connect_to(start_sock)
            else:
                start_sock.connect_to(new_node.in_socket)
            
            return

        if new_node:
            self.spawn_node(new_node, scene_pos)
            
            # Logika Auto-Connect yang sudah kita buat
            start_sock = self.scene().start_socket
            target_sockets = new_node.inputs if not start_sock.is_input else new_node.outputs
            
            for target_sock in target_sockets:
                if self._is_connection_allowed(start_sock, target_sock):
                    if start_sock.is_input:
                        target_sock.connect_to(start_sock)
                    else:
                        start_sock.connect_to(target_sock)
                    break
    
    def _is_connection_allowed(self, out_sock, in_sock):
        # Dasar: Harus beda (Input vs Output) dan Beda Node
        if out_sock.is_input == in_sock.is_input: return False
        if out_sock.parent_node == in_sock.parent_node: return False
        
        # Strict Typing: Exec hanya ke Exec, Data hanya ke Data yang tipenya sama
        if out_sock.is_exec != in_sock.is_exec:
            return False
        if (out_sock.is_exec == in_sock.is_exec == False) and (out_sock.data_type != in_sock.data_type):
            return False
            
        return True
    
    def _get_context_menu(self, scene_pos):
        """Helper untuk membangun menu klik kanan yang dinamis"""
        menu = QMenu()
        
        # 1. Menu Dialogue
        act_dial = menu.addAction("Add Dialogue Node")
        
        # 2. Menu Set Variable (dengan Sub-menu)
        set_var_menu = menu.addMenu("Add Set Variable")
        variables = self.main_window.var_manager.global_variables
        
        if not variables:
            set_var_menu.setEnabled(False)
            set_var_menu.setToolTip("Create a variable in the left panel first")
        else:
            # Buat sub-menu untuk setiap variabel yang tersedia
            for var_name in variables.keys():
                action = set_var_menu.addAction(f"Set {var_name} ({DataType(variables[var_name]['type']).value})")
                # Kita simpan nama variabel di dalam data action agar bisa diambil nanti
                action.setData(var_name)
        
        # 3. Menu Reroute
        menu.addSeparator()
        act_reroute = menu.addAction("Add Reroute")
        
        return menu, act_dial, set_var_menu, act_reroute
    
    def spawn_node(self, node, pos):
        """Helper untuk menaruh node di scene dan menampilkannya"""
        node.setPos(pos)
        self.scene().addItem(node)
        self.scene().clearSelection()
        node.setSelected(True)
        self.main_window.properties_panel.load_node(node)
        return node

    def _create_reroute_on_edge(self, edge, pos):
        """Menyisipkan reroute node di tengah kabel"""
        start_socket = edge.start_socket
        end_socket = edge.end_socket
        s_exec = start_socket.is_exec
        s_type = start_socket.data_type

        # 1. Buat Reroute Node baru
        reroute = RerouteNode(is_exec=s_exec, socket_data_type=s_type)
        reroute.setPos(pos.x() - 10, pos.y() - 10)
        self.scene().addItem(reroute)

        # 2. Hapus kabel lama
        self.scene().removeItem(edge)
        start_socket.edges.remove(edge)
        end_socket.edges.remove(edge)

        # 3. Buat dua kabel baru (Sambungkan Start -> Reroute -> End)
        start_socket.connect_to(reroute.in_socket)
        reroute.out_socket.connect_to(end_socket)
    
    #endregion Helpers