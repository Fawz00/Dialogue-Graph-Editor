import sys
from PyQt6.QtWidgets import (QLabel, QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox, QGroupBox, QVBoxLayout, QFrame)
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtCore import Qt

from Core.Enums.DataType import DataType
from Style import STYLES

class PropertyWidgetFactory:
    @staticmethod
    def create(layout, var_name, config, on_changed_callback, path=None):
        """
        Menghasilkan widget berdasarkan tipe data.
        on_changed_callback(path, value): fungsi yang dijalankan saat nilai widget berubah.
        """

        if path is None:
            path = []
        
        data_type = DataType(config.get("type"))
        current_value = config.get("value")

        if data_type not in (DataType.STRUCT, DataType.LIST):
            layout.addWidget(QLabel(f"{var_name}:"))

        # ---------- STRING ----------
        if data_type == DataType.STRING:
            w = QLineEdit(str(current_value))
            w.editingFinished.connect(
                lambda p=path: on_changed_callback(p, w.text())
            )
            layout.addWidget(w)
            return w

        # ---------- INT ----------
        elif data_type == DataType.INT:
            w = QSpinBox()
            w.setRange(-999999, 999999)
            try:
                w.setValue(int(current_value or 0))
            except:
                w.setValue(0)

            w.editingFinished.connect(
                lambda p=path: on_changed_callback(p, w.value())
            )
            layout.addWidget(w)
            return w

        # ---------- FLOAT ----------
        elif data_type == DataType.FLOAT:
            w = QDoubleSpinBox()
            try:
                w.setValue(float(current_value or 0.0))
            except:
                w.setValue(0.0)

            w.editingFinished.connect(
                lambda p=path: on_changed_callback(p, w.value())
            )
            layout.addWidget(w)
            return w

        # ---------- BOOL ----------
        elif data_type == DataType.BOOL:
            w = QCheckBox()
            w.setChecked(bool(current_value))
            w.stateChanged.connect(
                lambda state, p=path: on_changed_callback(p, bool(state))
            )
            layout.addWidget(w)
            return w

        # ---------- ENUM ----------
        elif data_type == DataType.ENUM:
            w = QComboBox()
            options = config.get("options", [])
            if options:
                w.addItems(options)
            w.setCurrentText(str(current_value))
            w.currentTextChanged.connect(
                lambda v, p=path: on_changed_callback(p, v)
            )
            layout.addWidget(w)
            return w

        # ---------- LIST ----------
        elif data_type == DataType.LIST:
            group = QGroupBox(var_name)
            group_layout = QVBoxLayout(group)

            list_type = config.get("list_type", DataType.STRING)

            for idx, item_value in enumerate(current_value):
                item_config = {
                    "type": list_type,
                    "value": item_value
                }

                item_path = path + [idx]

                PropertyWidgetFactory.create(
                    group_layout,
                    str(idx),
                    item_config,
                    on_changed_callback,
                    item_path
                )

            layout.addWidget(group)
            return group

        # ---------- STRUCT ----------
        elif data_type == DataType.STRUCT:
            group = QGroupBox(var_name)
            group_layout = QVBoxLayout(group)

            for sub_key, sub_config in current_value.items():
                sub_path = path + [sub_key]

                PropertyWidgetFactory.create(
                    group_layout,
                    sub_key,
                    sub_config,
                    on_changed_callback,
                    sub_path
                )

            layout.addWidget(group)
            return group
            
        return PropertyWidgetFactory.create_fallback_widget(current_value) # Fallback
    
    def create_fallback_widget(current_value):
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.NoFrame)  # matikan frame default
        frame.setAutoFillBackground(True)

        layout = QVBoxLayout(frame)
        label = QLabel(str(current_value))
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

        # Simpel: border + rounded + background
        color_border = "red"
        color_bg = "#ffc8c8"
        radius = 8
        frame.setStyleSheet(f"""
            border: 2px solid {color_border};
            border-radius: {radius}px;
            background-color: {color_bg};
        """)
        
        return frame