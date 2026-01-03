from PyQt6.QtCore import QObject, pyqtSignal

from Core.Debug import Debug
from Core.Enums.DataType import DataType

class VariableManager(QObject):
    # Konstanta untuk konfigurasi variabel
    _DEFAULT_VALUES = {
        DataType.STRING: "",
        DataType.INT: 0,
        DataType.FLOAT: 0.0,
        DataType.BOOL: False,
        DataType.STRUCT: {},
        DataType.LIST: [],
        DataType.ENUM: [],
        DataType.CLASS: {}
    }
    '''Berisi nilai default untuk tiap tipe data.\n
    Gunakan DataType sebagai key, misal: `DEFAULT_VALUES[DataType.INT]` -> 0.\n
    Atau gunakan seperti ini jika string: `DEFAULT_VALUES[DataType(DataType.INT.value)]` -> 0.
    '''

    SUPPORTED_TYPES_AS_STRING = list(dt.value for dt in _DEFAULT_VALUES.keys())

    # Event signal untuk perubahan variabel
    variable_created = pyqtSignal(str)
    variable_updated = pyqtSignal(str, str)
    variable_deleted = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        # Struktur: 
        # {
        #     "Variable": { <variable name>
        #         "type": DataType.ENUM, <DataType>
        #         "options": enum_values, <list>
        #         "value": self.selected_var <string>
        #     },
        #     "Advanced Settings": { <variable name>
        #         "type": DataType.STRUCT, <DataType>
        #         "value": { <nested properties>
        #             "Priority": {"type": DataType.INT, "value": 1},
        #             "Interpolate": {"type": DataType.BOOL, "value": False},
        #             "Test Float": {"type": DataType.FLOAT, "value": 0.0},
        #             "Test List": {"type": DataType.LIST, "value": []},
        #             "Text": {"type": DataType.STRING, "value": "None"},
        #             "Example list":
        #             {
        #                 "type": DataType.LIST,
        #                 "list_type": DataType.STRING,
        #                 "value": ["Item1", "Item2"]
        #             }
        #         }
        #     }
        # }
        self.global_variables = {
            "Variable": {
                "type": DataType.ENUM,
                "options": ["Var1", "Var2", "Var3"],
                "value": "Var1"
            },
            "Advanced Settings": {
                "type": DataType.STRUCT,
                "value": {
                    "Priority": {"type": DataType.INT, "value": 1},
                    "Interpolate": {"type": DataType.BOOL, "value": False},
                    "Test Float": {"type": DataType.FLOAT, "value": 0.0},
                    "Text": {"type": DataType.STRING, "value": "None"},
                    "Example list":
                    {
                        "type": DataType.LIST,
                        "list_type": DataType.STRING,
                        "value": ["Item1", "Item2"]
                    }
                }
            }
        }
    
    @staticmethod
    def get_default_value(var_type: str | DataType):
        """Mengembalikan nilai default berdasarkan tipe data"""
        dt = DataType(var_type)
        result = VariableManager._DEFAULT_VALUES.get(dt, None)
        return result
    
    # === CRUD Methods ===
    
    def delete_variable(self, name):
        if name in self.global_variables:
            del self.global_variables[name]
            self.variable_deleted.emit(name)
    
    def edit_variable(self, value_path: list, new_name: str = None, new_type: DataType = None, new_value=None):
        if not value_path:
            return

        # ===============================
        # Fungsi rekursif untuk navigasi & update
        # ===============================
        def recursive_update(parent, path):
            key = path[0]
            is_last = len(path) == 1

            # Tentukan current target
            if isinstance(parent, dict):
                if key not in parent:
                    return
                current = parent[key]
            elif isinstance(parent, list):
                if not (isinstance(key, int) and 0 <= key < len(parent)):
                    return
                current = parent[key]
            else:
                return

            if is_last:
                # ===============================
                # Level target: update name, type, value
                # ===============================
                # 1. Rename (hanya berlaku untuk dict key, bukan list item)
                if new_name and isinstance(parent, dict) and new_name != key:
                    parent[new_name] = current
                    del parent[key]
                    key = new_name
                    current = parent[key]

                # 2. Update type
                if new_type is not None:
                    new_type_value = DataType(new_type).value
                    old_type_value = DataType(current["type"]).value
                    if new_type_value != old_type_value:
                        current["type"] = DataType(new_type_value)
                        current["value"] = self.get_default_value(new_type_value)

                # 3. Update value
                if new_value is not None:
                    final_type_value = DataType(current["type"]).value
                    if VariableManager.is_value_valid(final_type_value, {"value": new_value}):
                        current["value"] = new_value

                return current

            # ===============================
            # Rekursi ke level berikutnya
            # ===============================
            next_parent = None
            if isinstance(current, dict) and "value" in current:
                next_parent = current["value"]
            elif isinstance(current, list) and all(isinstance(i, dict) and "type" in i for i in current):
                next_parent = current  # list of structs
            else:
                return

            recursive_update(next_parent, path[1:])

        # Mulai dari top-level global_variables
        recursive_update(self.global_variables, value_path)

        # Emit update untuk path top-level
        top_name = value_path[0]
        final_name = new_name if new_name and len(value_path) == 1 else top_name
        self.variable_updated.emit(top_name, final_name)
    
    def create_variable(self, name, var_type, value=None):
        if name in self.global_variables:
            return  # Sudah ada
        
        self.global_variables[name] = {
            'type': DataType(var_type),
            'value': VariableManager.get_default_value(var_type) if value is None else value
        }

        if value is not None:
            self.global_variables[name]['value'] = value

        self.variable_created.emit(name)
    
    @staticmethod
    def is_value_valid(dtype, meta: dict) -> bool:
        """
        Mengecek apakah value valid untuk DataType tertentu
        berdasarkan metadata variabel.
        """

        try:
            # ===============================
            # NORMALISASI TYPE
            # ===============================
            if isinstance(dtype, str):
                dtype = DataType(dtype)

            value = meta.get("value")

            # ===============================
            # PRIMITIVE TYPES
            # ===============================
            if dtype == DataType.STRING:
                return isinstance(str(value), str)

            if dtype == DataType.INT:
                try:
                    int(value)
                    return True
                except:
                    return False

            if dtype == DataType.FLOAT:
                try:
                    float(value)
                    return True
                except:
                    return False

            if dtype == DataType.BOOL:
                return isinstance(bool(value), bool)

            # ===============================
            # ENUM
            # ===============================
            if dtype == DataType.ENUM:
                options = meta.get("options", [])
                return isinstance(options, list) and value in options

            # ===============================
            # LIST
            # ===============================
            if dtype == DataType.LIST:
                if not isinstance(value, list):
                    return False

                list_type = meta.get("list_type")
                if not list_type:
                    return True

                for item in value:
                    if not VariableManager.is_value_valid(list_type, {"value": item}):
                        return False
                return True

            # ===============================
            # STRUCT
            # ===============================
            if dtype == DataType.STRUCT:
                if not isinstance(value, dict):
                    return False

                structure = meta.get("structure")
                if not structure:
                    return True

                for key, field_meta in structure.items():
                    if key not in value:
                        return False

                    field_type = field_meta.get("type")
                    field_value = value[key]

                    if not VariableManager.is_value_valid(field_type, {"value": field_value}):
                        return False
                return True

            # ===============================
            # CLASS
            # ===============================
            if dtype == DataType.CLASS:
                class_name = meta.get("class_name")
                if not class_name:
                    return False

                if isinstance(value, str):
                    return True

                return value.__class__.__name__ == class_name

        except Exception:
            return False

        return False

