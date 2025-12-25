from PyQt6.QtCore import QObject, pyqtSignal

class VariableManager(QObject):
    # Konstanta untuk konfigurasi variabel
    VAR_CONFIG = {
        "String": "",
        "Integer": 0,
        "Float": 0.0,
        "Boolean": False
    }

    SUPPORTED_TYPES = list(VAR_CONFIG.keys())

    # Event signal untuk perubahan variabel
    variable_created = pyqtSignal(str)
    variable_updated = pyqtSignal(str, str)
    variable_deleted = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        # Struktur: {'nama_var': {'type': 'String', 'value': 'Default'}}
        self.variables = {}