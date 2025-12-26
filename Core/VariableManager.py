from PyQt6.QtCore import QObject, pyqtSignal

from Core.Enums.DataType import DataType

class VariableManager(QObject):
    # Konstanta untuk konfigurasi variabel
    DEFAULT_VALUES = {
        DataType.STRING: "",
        DataType.INT: 0,
        DataType.FLOAT: 0.0,
        DataType.BOOL: False,
        DataType.STRUCT: {},
        DataType.LIST: []
    }
    '''Berisi nilai default untuk tiap tipe data.\n
    Gunakan DataType sebagai key, misal: `DEFAULT_VALUES[DataType.INT]` -> 0.\n
    Atau gunakan seperti ini jika string: `DEFAULT_VALUES[DataType(DataType.INT.value)]` -> 0.
    '''

    SUPPORTED_TYPES = list(dt.value for dt in DEFAULT_VALUES.keys())

    # Event signal untuk perubahan variabel
    variable_created = pyqtSignal(str)
    variable_updated = pyqtSignal(str, str)
    variable_deleted = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        # Struktur: {'nama_var': {'type': 'String', 'value': 'Default'}}
        self.global_variables = {}