from PyQt6.QtWidgets import QStyledItemDelegate, QComboBox
from PyQt6.QtCore import Qt

from Core.VariableManager import VariableManager

class TypeDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        # Hanya kolom index 1 (kolom Type) yang pakai dropdown
        editor = QComboBox(parent)
        editor.addItems(VariableManager.SUPPORTED_TYPES_AS_STRING)
        return editor

    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.ItemDataRole.EditRole)
        if value:
            editor.setCurrentText(value)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentText(), Qt.ItemDataRole.EditRole)