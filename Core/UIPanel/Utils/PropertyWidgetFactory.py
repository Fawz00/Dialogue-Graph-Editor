import sys
from PyQt6.QtWidgets import (QLabel, QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox, QGroupBox, QVBoxLayout, QFrame)
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtCore import Qt

from Core.Enums.DataType import DataType
from Style import STYLES

class PropertyWidgetFactory:
    @staticmethod
    def create(layout, data_type, var_name, current_value, on_changed_callback, options=None):
        """
        Menghasilkan widget berdasarkan tipe data.
        on_changed_callback: fungsi yang dijalankan saat nilai widget berubah.
        """
        if data_type != DataType.STRUCT: # Struct biasanya pakai GroupBox, tidak butuh label samping
            layout.addWidget(QLabel(f"{var_name}:"))

        if data_type == DataType.STRING:
            w = QLineEdit(str(current_value))
            w.textChanged.connect(on_changed_callback)
            layout.addWidget(w)
            return w

        elif data_type == DataType.INT:
            w = QSpinBox()
            w.setRange(-999999, 999999)
            w.setValue(int(current_value if current_value is not None and current_value != "" else 0))
            w.valueChanged.connect(on_changed_callback)
            layout.addWidget(w)
            return w

        elif data_type == DataType.FLOAT:
            w = QDoubleSpinBox()
            w.setValue(float(current_value if current_value is not None and current_value != "" else 0.0))
            w.valueChanged.connect(on_changed_callback)
            layout.addWidget(w)
            return w

        elif data_type == DataType.BOOL:
            w = QCheckBox()
            w.setChecked(bool(current_value))
            w.stateChanged.connect(lambda state: on_changed_callback(bool(state)))
            layout.addWidget(w)
            return w

        elif data_type == DataType.ENUM:
            w = QComboBox()
            if options: w.addItems(options)
            w.setCurrentText(str(current_value))
            w.currentTextChanged.connect(on_changed_callback)
            layout.addWidget(w)
            return w

        elif data_type == DataType.STRUCT:
            # Recursive call untuk Collapsible List (GroupBox)
            group = QGroupBox(var_name)
            group_layout = QVBoxLayout(group)
            for sub_key, sub_config in current_value.items():
                group_layout.addWidget(PropertyWidgetFactory.create(group_layout, sub_config['type'], sub_key, sub_config['value'], lambda v, k=sub_key: on_changed_callback(k, v), sub_config.get('options')))
            return group # Return langsung groupbox
            
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