from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional

from typing import cast
from PyQt6.QtWidgets import (QWidget, QLabel, QVBoxLayout, QHBoxLayout, QMessageBox)
from PyQt6.QtWidgets import QScrollArea

from Core.EventSystem.EventType import EventType
from Core.Graph.BaseNode import BaseNode
from Core.Structures.Variable import ValueType, Variable
from Core.UIPanelBase import UIPanelBase
from Core.Enums.DataType import DataType
from Core.UIPanel.Utils.PropertyWidgetFactory import PropertyWidgetFactory
from Core.VariableManager import VariableManager
from Core.EventSystem.Event import Event

if TYPE_CHECKING:
    from Main import MainWindow


class DataFieldType(Enum):
    Invalid = "invalid"
    GlobalVariable = "global_var"
    Node = "node"

@dataclass
class DataField:
    type: DataFieldType
    var_name: Optional[str] = None
    node_obj: Optional[BaseNode] = None

class PropertiesPanel(UIPanelBase):
    def __init__(self, main_window: MainWindow):
        super().__init__(main_window)
        self.target_data: DataField = DataField(type=DataFieldType.Invalid)

        main_window.event_bus.subscribe(EventType.EVENT_VARIABLE_UPDATED.value, self._on_variable_updated)
        main_window.event_bus.subscribe(EventType.EVENT_VARIABLE_ADDED.value, self._on_variable_created)
        main_window.event_bus.subscribe(EventType.EVENT_VARIABLE_REMOVED.value, self._on_variable_deleted)
    
    # ========== Event Handlers ==========
    def _on_variable_created(self, event: Event):
        self.refresh()
    def _on_variable_deleted(self, event: Event):
        self.refresh()
    def _on_variable_updated(self, event: Event):
        self.refresh()

    def clear(self):
        # Bersihkan layout
        while self.v_layout.count():
            child = self.v_layout.takeAt(0)
            widget = child.widget() if child is not None else None
            if widget is not None:
                widget.deleteLater()

    def load_variable(self, name: str | None):
        """Menampilkan detail variabel global"""
        if name is None:
            self.target_data = DataField(type=DataFieldType.Invalid)
            self.refresh()
            return

        if self.var_manager.get_global_variable(name) is None:
            self.target_data = DataField(type=DataFieldType.Invalid)
            self.refresh()
            return
        
        scene = self.main_window.view.scene()
        if scene:
            scene.clearSelection()
        self.target_data = DataField(type=DataFieldType.GlobalVariable, var_name=name)
        self.refresh()

    def load_node(self, node: BaseNode | None):
        """Menampilkan detail node (logika lama)"""
        if node is None:
            self.target_data = DataField(type=DataFieldType.Invalid)
            self.refresh()
            return

        self.target_data = DataField(type=DataFieldType.Node, node_obj=node)
        self.refresh()

    def update_prop(self, path: list[str], value: ValueType):
        if not self.target_data:
            return

        if self.target_data.type == DataFieldType.Node:
            node = self.target_data.node_obj
            if node is None:
                return
            node.set_property(path, value)

            self.refresh()

        elif self.target_data.type == DataFieldType.GlobalVariable:
            old_name = self.target_data.var_name
            if old_name is None:
                return

            new_name = None
            new_type = None
            new_value = None
            new_other_props: dict[str, Any] = {}

            if path[0] == "var_name":
                new_name = str(value) if isinstance(value, str) else None
            elif path[0] == "var_type":
                new_type = DataType(value)
            elif path[0] == "default_value":
                new_value = value
            elif path[0] == "element_type":
                new_other_props["element_type"] = DataType(value)
            
            # Validasi
            if new_name != old_name and new_name is not None and self.var_manager.get_global_variable(new_name) is not None:
                QMessageBox.warning(self, "Rename Error", f"Name '{new_name}' is already in use!")
                new_name = None
            
            # Update variable
            full_path: list[str] = [old_name, *path[1:]]
            new_data = Variable(
                type=new_type,
                value=new_value,
                options=new_other_props.get("options"),
                element_type=new_other_props.get("element_type")
            )

            self.var_manager.edit_global_variable(
                value_path=full_path,
                new_name=new_name,
                new_data=new_data
            )
    
    def refresh(self):
        # Bersihkan layout
        self.clear()
            
        if not self.target_data: return
        if (
            self.target_data.type == DataFieldType.GlobalVariable
            and (
                self.target_data.var_name is None
                or self.var_manager.get_global_variable(self.target_data.var_name) is None
            )
        ):
                self.target_data = DataField(type=DataFieldType.Invalid)
                return

        property_title = QLabel("<b>Properties</b>")
        if self.target_data.type == DataFieldType.Node:
            node_title = self.target_data.node_obj.title if self.target_data.node_obj else "Unknown"
            property_title.setText(f"<b>Node: {node_title}</b>")
        elif self.target_data.type == DataFieldType.GlobalVariable:
            property_title.setText(f"<b>Global Variable: {self.target_data.var_name}</b>")
        else:
            property_title.setText("<b>Properties</b>")

        property_title.setStyleSheet("color: yellow;")
        self.v_layout.addWidget(property_title)
        
        # Render berdasarkan tipe target data
        if self.target_data.type == DataFieldType.Node:

            selected_node = self.target_data.node_obj
            if not selected_node:
                return
            
            schema = selected_node.get_properties()
            self.render_widgets(
                self.v_layout,
                schema,
            )

        elif self.target_data.type == DataFieldType.GlobalVariable:
            self.render_variable_properties()
    
    def render_widgets(self, layout: QVBoxLayout, schema: dict[str, Variable]):
        """Factory untuk membuat widget berdasarkan tipe data dengan scrollable area"""
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        inner_widget = QWidget()
        inner_layout = QVBoxLayout(inner_widget)
        inner_layout.setContentsMargins(8, 8, 8, 8)

        for name, conf in schema.items():
            t = DataType(conf.type)

            container = QWidget()
            h_layout = QHBoxLayout(container)
            h_layout.setContentsMargins(0, 2, 0, 2)

            # Buat widget properti berdasarkan tipe data
            widget = PropertyWidgetFactory.create(
                h_layout,
                name,
                conf,
                lambda v, k=[name]: self.update_prop(v, k),
                [name]
            )
            if t == DataType.STRUCT and widget:
                inner_layout.addWidget(widget)  # Sudah return GroupBox langsung
            else:
                inner_layout.addWidget(container)

        inner_layout.addStretch()
        scroll_area.setWidget(inner_widget)
        self.v_layout.addWidget(scroll_area)

    def render_variable_properties(self):
        """Membuat UI untuk edit variabel global"""
        name = self.target_data.var_name
        if name is None:
            return
        data = self.main_window.var_manager.get_global_variable(name)
        data = cast(Variable, data)

        # Serialize structure
        variable_serializer = {
            "var_name": Variable(
                display_name="Name",
                type=DataType.STRING,
                value=name
            ),
            "var_type": Variable(
                display_name="Type",
                type=DataType.ENUM,
                options=VariableManager.SUPPORTED_TYPES_AS_STRING,
                value=DataType(data.type).value
            ),
            # If array add element type
            **({
                "element_type": Variable(
                    display_name="Element Type",
                    type=DataType.ENUM,
                    options=VariableManager.PRIMITIVE_TYPES_AS_STRING,
                    value=DataType(data.element_type if data.element_type is not None else DataType.STRING).value
                )
            } if DataType(data.type) == DataType.ARRAY else {}),
            "default_value": Variable(
                display_name="Default Value",
                type=DataType(data.type),
                options=data.options if data.options is not None else None,
                element_type=DataType(data.element_type) if data.element_type is not None else None,
                value=data.value
            )
        }

        self.render_widgets(
            self.v_layout,
            variable_serializer
        )
