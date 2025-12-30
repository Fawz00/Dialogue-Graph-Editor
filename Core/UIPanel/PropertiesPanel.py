import sys
from PyQt6.QtWidgets import (QWidget, QLabel, QLineEdit, QComboBox, QFormLayout, QVBoxLayout,
                             QHBoxLayout, QSpinBox, QCheckBox, QDoubleSpinBox, QGroupBox)

from Core.UIPanelBase import UIPanelBase
from Core.Enums.DataType import DataType
from Core.UIPanel.Utils.PropertyWidgetFactory import PropertyWidgetFactory
from Core.VariableManager import VariableManager

class PropertiesPanel(UIPanelBase):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.target_data = None

    def clear(self):
        # Bersihkan layout
        while self.layout.count():
            child = self.layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()

    def load_variable(self, name):
        """Menampilkan detail variabel global"""
        if name is None:
            self.target_data = None
            self.refresh()
            return

        if name not in self.var_manager.global_variables:
            self.target_data = None
            self.refresh()
            return
        
        self.target_data = {"type": "global_var", "name": name}
        self.refresh()

    def load_node(self, node):
        """Menampilkan detail node (logika lama)"""
        if node is None:
            self.target_data = None
            self.refresh()
            return

        self.target_data = {"type": "node", "obj": node}
        self.refresh()

    def update_prop(self, key, value):
        if self.target_data["type"] == "node":
            self.target_data["obj"].set_property(key, value)
            self.refresh()
        elif self.target_data["type"] == "global_var":
            var_name = self.target_data["name"]
            var_data = self.var_manager.global_variables[var_name]
            
            new_name = var_name
            new_type = var_data["type"]
            new_value = var_data["value"]

            if key == "Name":
                new_name = value
                self.target_data["name"] = new_name
                self.var_manager.edit_variable(
                    var_name,
                    new_name=new_name
                )
            elif key == "Type":
                new_type = DataType(value)
                self.var_manager.edit_variable(
                    var_name,
                    new_type=new_type
                )
            elif key == "Default Value":
                new_value = value
                self.var_manager.edit_variable(
                    var_name,
                    new_value=new_value
                )

            self.refresh()
    
    def refresh(self):
        # Bersihkan layout
        self.clear()
            
        if not self.target_data: return
        if self.target_data["type"] == "global_var" and self.target_data["name"] not in self.var_manager.global_variables:
                self.target_data = None
                return

        property_title = QLabel("<b>Properties</b>")
        if self.target_data["type"] == "node":
            property_title.setText(f"<b>Node: {self.target_data['obj'].title}</b>")
        elif self.target_data["type"] == "global_var":
            property_title.setText(f"<b>Global Variable: {self.target_data['name']}</b>")
        else:
            property_title.setText("<b>Properties</b>")

        property_title.setStyleSheet("color: yellow;")
        self.layout.addWidget(property_title)
        
        # Render berdasarkan tipe target data
        if self.target_data["type"] == "node":

            selected_node = self.target_data["obj"]
            if not selected_node:
                return
            
            schema = selected_node.get_properties()
            self.render_widgets(
                self.layout,
                schema,
            )

        elif self.target_data["type"] == "global_var":
            self.render_variable_properties()
    
    def render_widgets(self, layout, schema):
        """Factory untuk membuat widget berdasarkan tipe data"""
        for name, conf in schema.items():
            t = conf.get("type")

            container = QWidget()
            layout = QHBoxLayout(container)
            layout.setContentsMargins(0, 2, 0, 2)

            # Buat widget properti berdasarkan tipe data
            widget = PropertyWidgetFactory.create(
                layout,
                name,
                conf,
                lambda v, k=name: self.update_prop(k, v)
            )
            if t == DataType.STRUCT and widget:
                self.layout.addWidget(widget)  # Sudah return GroupBox langsung
            else:
                self.layout.addWidget(container)
        
        self.layout.addStretch()

    def render_variable_properties(self):
        """Membuat UI untuk edit variabel global"""
        name = self.target_data["name"]
        data = self.main_window.var_manager.global_variables.get(name)
        
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 2, 0, 2)

        # Serialize structure
        variable_serializer = {
            "Name": {
                "type": DataType.STRING,
                "value": name
            },
            "Type": {
                "type": DataType.ENUM,
                "options": VariableManager.SUPPORTED_TYPES_AS_STRING,
                "value": DataType(data['type']).value
            },
            "Default Value": {
                "type": DataType(data['type']),
                "options": data['options'] if 'options' in data else None,
                "list_type": DataType(data['list_type']) if 'list_type' in data else None,
                "value": data['value']
            }
        }

        self.render_widgets(
            self.layout,
            variable_serializer
        )
