import sys
from PyQt6.QtWidgets import (QWidget, QLabel, QLineEdit, QComboBox, QFormLayout, QVBoxLayout,
                             QHBoxLayout, QSpinBox, QCheckBox, QDoubleSpinBox, QGroupBox)

from Core.Enums.DataType import DataType
from Core.UIPanel.Utils.PropertyWidgetFactory import PropertyWidgetFactory

class PropertiesPanel(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.layout = QVBoxLayout(self)
        self.current_node = None

    def clear(self):
        # Bersihkan layout
        while self.layout.count():
            child = self.layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()

    def load_node(self, node):
        self.current_node = node
        self.refresh()

    def update_prop(self, key, value):
        if self.current_node:
            self.current_node.set_property(key, value)
    
    def refresh(self):
        # Bersihkan layout
        self.clear()
            
        if not self.current_node: return
        
        # Ambil schema dari node
        schema = self.current_node.get_properties()
        for key, config in schema.items():
            widget = self.create_property_widget(key, config)
            self.layout.addWidget(widget)
        self.layout.addStretch()
    
    def create_property_widget(self, key, config):
        """Factory untuk membuat widget berdasarkan tipe data"""
        t = config.get("type")
        val = config.get("value")
        
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 2, 0, 2)

        # --- LOGIKA MAPPING TIPE KE WIDGET ---
        
        widget = PropertyWidgetFactory.create(
            layout,
            t,
            key,
            val,
            lambda v, k=key: self.update_prop(k, v),
            config.get("options")
        )
        if t == DataType.STRUCT and widget:
            return widget  # Sudah return GroupBox langsung

        return container