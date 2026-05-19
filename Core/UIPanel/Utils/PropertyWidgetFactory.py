from typing import Any, Callable, cast
from PyQt6.QtWidgets import (QBoxLayout, QLabel, QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox, QVBoxLayout, QHBoxLayout, QFrame, QWidget, QToolButton, QMenu)
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import Qt, QSize

from Core.Enums.DataType import DataType
from Core.Structures.Variable import Variable
from Core.VariableManager import VariableManager
from Style import STYLES

class PropertyWidgetFactory:
    @staticmethod
    def create(layout: QBoxLayout, var_name: str, config: Variable, on_changed_callback: Callable[[list[str], Any], None], path: list[str] = []):
        """
        Menghasilkan widget berdasarkan tipe data.
        on_changed_callback(path, value): fungsi yang dijalankan saat nilai widget berubah.
        """
        if config.enabled is False:
            return None

        data_type = DataType(config.type)
        current_value = config.value

        display_name = config.display_name or var_name

        if data_type not in (DataType.STRUCT, DataType.ARRAY, DataType.LIST):
            layout.addWidget(QLabel(f"{display_name}:"))

        # ---------- STRING ----------
        if data_type == DataType.STRING:
            w = QLineEdit(str(current_value))
            def on_editing_finished() -> None:
                on_changed_callback(path, w.text())

            w.editingFinished.connect(on_editing_finished) # type: ignore
            layout.addWidget(w)
            return w

        # ---------- INT ----------
        elif data_type == DataType.INT:
            w = QSpinBox()
            w.setRange(-2147483648, 2147483647)
            try:
                w.setValue(int(current_value or 0))
            except:
                w.setValue(0)

            def on_editing_finished() -> None:
                on_changed_callback(path, w.value())

            w.editingFinished.connect(on_editing_finished) # type: ignore
            layout.addWidget(w)
            return w

        # ---------- FLOAT ----------
        elif data_type == DataType.FLOAT:
            w = QDoubleSpinBox()
            w.setDecimals(6)
            w.setRange(-2147483648.0, 2147483647.0)
            try:
                w.setValue(float(current_value or 0.0))
            except:
                w.setValue(0.0)

            def on_editing_finished() -> None:
                on_changed_callback(path, w.value())

            w.editingFinished.connect(on_editing_finished) # type: ignore
            layout.addWidget(w)
            return w

        # ---------- BOOL ----------
        elif data_type == DataType.BOOL:
            w = QCheckBox()
            w.setChecked(bool(current_value))

            def on_state_changed(state: Any) -> None:
                on_changed_callback(path, bool(state))

            w.stateChanged.connect(on_state_changed) # type: ignore
            layout.addWidget(w)
            return w

        # ---------- ENUM ----------
        elif data_type == DataType.ENUM:
            w = QComboBox()
            # Ensure options are strings so addItems has a known Iterable[str]
            options = [str(o) for o in (config.options or [])]
            if options:
                w.addItems(options) # type: ignore
            w.setCurrentText(str(current_value))

            def on_current_text_changed(text: str) -> None:
                on_changed_callback(path, text)

            w.currentTextChanged.connect(on_current_text_changed) # type: ignore
            layout.addWidget(w)
            return w

        # ---------- ARRAY ----------
        elif data_type == DataType.ARRAY:
            section, content_layout = PropertyWidgetFactory._create_collapsible_section(display_name)

            element_type = config.element_type or DataType.STRING
            current_value = cast(list[str], current_value)

            for idx, item_value in enumerate(current_value):
                row = QHBoxLayout()

                item_config = Variable(
                    type=element_type,
                    value=item_value
                )
                item_path = path + [cast(str, idx)]

                PropertyWidgetFactory.create(
                    row,
                    str(idx),
                    item_config,
                    on_changed_callback,
                    item_path
                )

                PropertyWidgetFactory._create_item_action_button(
                    row,
                    idx,
                    item_path,
                    current_value,
                    on_changed_callback
                )

                content_layout.addLayout(row)

            def add_item():
                new_value = current_value + [
                    VariableManager.get_default_value(element_type)
                ]
                on_changed_callback(path, new_value)

            add_btn = QToolButton()
            add_btn.setText("Add")
            add_btn.setIcon(QIcon.fromTheme("list-add"))
            add_btn.clicked.connect(add_item) # type: ignore

            content_layout.addWidget(add_btn)
            layout.addWidget(section)
            return section

        # ---------- LIST ----------
        elif data_type == DataType.LIST:
            section, content_layout = PropertyWidgetFactory._create_collapsible_section(display_name)
            current_value = cast(list[str], current_value)
            element_type = config.element_type or DataType.STRING

            for idx, item_value in enumerate(current_value):
                item_config = Variable(
                    type=element_type,
                    value=item_value
                )
                item_path = path + [cast(str, idx)]

                PropertyWidgetFactory.create(
                    content_layout,
                    str(idx),
                    item_config,
                    on_changed_callback,
                    item_path
                )

            layout.addWidget(section)
            return section

        # ---------- STRUCT ----------
        elif data_type == DataType.STRUCT:
            section, content_layout = PropertyWidgetFactory._create_collapsible_section(display_name)

            for sub_key, sub_config in current_value.items():
                sub_path = path + [sub_key]

                PropertyWidgetFactory.create(
                    content_layout,
                    sub_key,
                    sub_config,
                    on_changed_callback,
                    sub_path
                )

            layout.addWidget(section)
            return section
            
        return PropertyWidgetFactory._create_fallback_widget(current_value) # Fallback
    
    # ===== HELPER METHODS =====
    #region Helper Methods

    @staticmethod
    def _create_item_action_button(
        parent_layout: QBoxLayout,
        index: int,
        path: list[str],
        current_list: list[str],
        on_changed_callback: Callable[[list[str], Any], None]
    ):
        btn = QToolButton()
        btn.setText("⋮")
        btn.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)

        menu = QMenu(btn)

        # Remove
        remove_action = QAction("Remove", btn)
        def remove():
            new_list = current_list[:index] + current_list[index+1:]
            on_changed_callback(path[:-1], new_list)
        remove_action.triggered.connect(remove) # type: ignore
        menu.addAction(remove_action) # type: ignore

        # Move Up
        if index > 0:
            up_action = QAction("Move Up", btn)
            def move_up():
                new_list = current_list[:]
                new_list[index-1], new_list[index] = new_list[index], new_list[index-1]
                on_changed_callback(path[:-1], new_list)
            up_action.triggered.connect(move_up) # type: ignore
            menu.addAction(up_action) # type: ignore

        # Move Down
        if index < len(current_list) - 1:
            down_action = QAction("Move Down", btn)
            def move_down():
                new_list = current_list[:]
                new_list[index+1], new_list[index] = new_list[index], new_list[index+1]
                on_changed_callback(path[:-1], new_list)
            down_action.triggered.connect(move_down) # type: ignore
            menu.addAction(down_action) # type: ignore

        btn.setMenu(menu)
        parent_layout.addWidget(btn)

    @staticmethod
    def _create_collapsible_section(title: str):
        header = QToolButton()
        header.setText(title)
        header.setCheckable(True)
        header.setChecked(True)
        header.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        header.setIconSize(QSize(10, 10))
        header.setIcon(QIcon("resources/arrow_down.png"))
        header.setStyleSheet(f"""
            QToolButton {{
                color: #{STYLES['text_color'].name()[1:]};
                border: none;
                font-weight: bold;
            }}
        """)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(15, 0, 0, 0)

        def toggle(checked: bool):
            content.setVisible(checked)
            header.setIcon(
                QIcon("resources/arrow_down.png") if checked
                else QIcon("resources/arrow_right.png")
            )

        header.toggled.connect(toggle) # type: ignore

        # Layout inner: header + separator + content
        inner_layout = QVBoxLayout()
        inner_layout.setContentsMargins(0, 0, 0, 0)
        inner_layout.setSpacing(2)
        inner_layout.addWidget(header)
        inner_layout.addWidget(content)

        inner_widget = QWidget()
        inner_widget.setLayout(inner_layout)

        # --- wrapper outline ---
        wrapper = QFrame()
        wrapper.setFrameShape(QFrame.Shape.Box)
        wrapper.setFrameShadow(QFrame.Shadow.Plain)
        wrapper.setLineWidth(1)
        wrapper.setMidLineWidth(0)

        wrapper_layout = QVBoxLayout(wrapper)
        wrapper_layout.setContentsMargins(4, 4, 4, 4)  # jarak dari border
        wrapper_layout.addWidget(inner_widget)

        return wrapper, content_layout

    @staticmethod
    def _create_fallback_widget(current_value: Any):
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
    
    #endregion Helper Methods