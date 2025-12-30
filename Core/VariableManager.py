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
        DataType.LIST: [],
        DataType.ENUM: [],
        DataType.CLASS: {}
    }
    '''Berisi nilai default untuk tiap tipe data.\n
    Gunakan DataType sebagai key, misal: `DEFAULT_VALUES[DataType.INT]` -> 0.\n
    Atau gunakan seperti ini jika string: `DEFAULT_VALUES[DataType(DataType.INT.value)]` -> 0.
    '''

    SUPPORTED_TYPES_AS_STRING = list(dt.value for dt in DEFAULT_VALUES.keys())

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
    
    def get_default_value(self, var_type):
        """Mengembalikan nilai default berdasarkan tipe data"""
        dt = DataType(var_type)
        result = VariableManager.DEFAULT_VALUES.get(dt, None)
        return result
    
    # === CRUD Methods ===
    
    def delete_variable(self, name):
        if name in self.global_variables:
            del self.global_variables[name]
            self.variable_deleted.emit(name)
    
    def edit_variable(self, old_name, new_name=None, new_type=None, new_value=None):
        if old_name not in self.global_variables:
            return
    
        var_data = self.global_variables.get(old_name)

        # ===============================
        # 1. Tentukan nama final
        # ===============================
        final_name = old_name
        if new_name and new_name.strip() and new_name != old_name:
            final_name = new_name.strip()
            self.global_variables[final_name] = var_data
            del self.global_variables[old_name]

        # ===============================
        # 2. Tentukan tipe final
        # ===============================
        final_type = var_data["type"]
        if new_type is not None or new_type != var_data["type"]:
            final_type = new_type

        # ===============================
        # 3. Tentukan value final
        # ===============================
        final_value = var_data["value"]
        if new_value is not None:
            if new_type is not None and new_type != var_data["type"]:
                # Tipe berubah, set ke default baru
                final_value = self.get_default_value(final_type)
            else:
                # Tipe sama, set ke value baru jika valid
                if VariableManager.is_value_valid(final_type, {"value": new_value}):
                    final_value = new_value
        else:
            # Jika value tidak diberikan, dan tipe berubah
            if new_type is not None and new_type != var_data["type"]:
                final_value = self.get_default_value(final_type)
        
        # Set data
        new_var = self.global_variables[final_name]
        new_var["type"] = final_type
        new_var["value"] = final_value

        # ===============================
        # 4. Emit update
        # ===============================
        self.variable_updated.emit(old_name, final_name)
    
    def create_variable(self, name, var_type, value=None):
        if name in self.global_variables:
            return  # Sudah ada
        
        self.global_variables[name] = {
            'type': var_type,
            'value': VariableManager.DEFAULT_VALUES[DataType(var_type)]
        }

        if value is not None:
            self.global_variables[name]['value'] = value

        self.variable_created.emit(name)
    
    @staticmethod
    def is_value_valid(dtype: DataType, meta: dict) -> bool:
        """
        Mengecek apakah value valid untuk DataType tertentu
        berdasarkan metadata variabel.
        """

        value = None

        try:
            value = meta.get("value")

            # ===============================
            # PRIMITIVE TYPES
            # ===============================
            if dtype == DataType.STRING:
                value = str(value)
                return isinstance(value, str)

            if dtype == DataType.INT:
                try:
                    value = int(value)
                except:
                    return False
                return isinstance(value, int)

            if dtype == DataType.FLOAT:
                try:
                    value = float(value)
                except:
                    return False
                return isinstance(value, float)

            if dtype == DataType.BOOL:
                try:
                    value = bool(value)
                except:
                    return False
                return isinstance(value, bool)

            # ===============================
            # ENUM
            # ===============================
            if dtype == DataType.ENUM:
                options = meta.get("options", [])
                if not isinstance(options, list):
                    return False
                # enum tanpa options → dianggap empty / invalid
                return value in options

            # ===============================
            # LIST
            # ===============================
            if dtype == DataType.LIST:
                if not isinstance(value, list):
                    return False

                list_type = meta.get("list_type")
                if not list_type:
                    # list tanpa list_type → list bebas
                    return True

                # cek tiap item sesuai list_type
                for item in value:
                    if not VariableManager.is_value_valid(list_type, item, {}):
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
                    # struct tanpa schema → any dict
                    return True

                # validasi tiap field berdasarkan schema
                for key, field_meta in structure.items():
                    if key not in value:
                        return False

                    field_type = field_meta.get("type")
                    field_value = value[key]

                    if not VariableManager.is_value_valid(field_type, field_value, field_meta):
                        return False

                return True

            # ===============================
            # CLASS
            # ===============================
            if dtype == DataType.CLASS:
                class_name = meta.get("class_name")
                if not class_name:
                    return False

                # value bisa string reference atau object instance
                if isinstance(value, str):
                    return True

                # fallback: instance check (opsional)
                try:
                    return value.__class__.__name__ == class_name
                except Exception:
                    return False
    
        except Exception:
            return False

        # ===============================
        # UNKNOWN TYPE
        # ===============================
        return False
