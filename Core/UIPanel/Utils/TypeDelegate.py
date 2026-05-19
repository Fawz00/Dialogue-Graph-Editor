from PyQt6.QtWidgets import QStyleOptionViewItem, QStyledItemDelegate, QComboBox, QWidget
from PyQt6.QtCore import QAbstractItemModel, QModelIndex, Qt

from Core.VariableManager import VariableManager

class TypeDelegate(QStyledItemDelegate):
    def createEditor(self, parent: QWidget | None, option: QStyleOptionViewItem | None, index: QModelIndex) -> QComboBox:
        # Hanya kolom index 1 (kolom Type) yang pakai dropdown
        editor = QComboBox(parent)
        editor.addItems(VariableManager.SUPPORTED_TYPES_AS_STRING) # type: ignore
        return editor

    def setEditorData(self, editor: QWidget | None, index: QModelIndex):
        model = index.model()
        if model is None or not isinstance(editor, QComboBox):
            return

        value = model.data(index, Qt.ItemDataRole.EditRole)
        if value:
            editor.setCurrentText(value)

    def setModelData(self, editor: QWidget | None, model: QAbstractItemModel | None, index: QModelIndex):
        if model is None or not isinstance(editor, QComboBox):
            return

        model.setData(index, editor.currentText(), Qt.ItemDataRole.EditRole)