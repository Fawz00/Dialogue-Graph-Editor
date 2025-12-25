import sys
from PyQt6.QtWidgets import (QWidget, QLabel, QLineEdit, 
                             QComboBox, QFormLayout)

class PropertiesPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QFormLayout()
        self.setLayout(self.layout)
        self.current_node = None

    def clear(self):
        self.current_node = None
        if self.layout is not None:
            while self.layout.count() > 0:
                # Ambil baris terakhir dan hapus
                self.layout.removeRow(0)
        self.update() # Paksa refresh visual

    def load_node(self, node):
        self.clear()
        self.current_node = node
        
        props = node.get_properties()
        
        label_type = QLabel(f"Type: {node.title}")
        label_type.setStyleSheet("font-weight: bold; color: orange;")
        self.layout.addRow(label_type)

        for key, data in props.items():
            if data['type'] == 'text':
                widget = QLineEdit(str(data['value']))
                widget.textChanged.connect(lambda val, k=key: self.update_node(k, val))
                self.layout.addRow(key, widget)
            elif data['type'] == 'list':
                widget = QLineEdit(str(data['value']))
                widget.setPlaceholderText("comma, separated, choices")
                widget.textChanged.connect(lambda val, k=key: self.update_node(k, val))
                self.layout.addRow(key, widget)
            elif data['type'] == 'enum':
                widget = QComboBox()
                widget.addItems(data['options'])
                widget.setCurrentText(data['value'])
                widget.currentTextChanged.connect(lambda val, k=key: self.update_node(k, val))
                self.layout.addRow(key, widget)

    def update_node(self, key, value):
        if self.current_node:
            self.current_node.set_property(key, value)
            self.current_node.update() # Paksa redraw node
    
    def refresh(self):
        """Memuat ulang UI jika ada perubahan data eksternal (seperti rename variabel)"""
        if self.current_node:
            # Simpan referensi node, bersihkan UI, lalu muat ulang
            node = self.current_node
            self.load_node(node)