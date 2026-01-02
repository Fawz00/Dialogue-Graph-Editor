from PyQt6.QtCore import QObject, pyqtSignal

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
    
    def edit_variable(self, old_name: str, new_name: str = None, new_type: DataType = None, new_value = None, value_path: list = None):
        if old_name not in self.global_variables:
            return
            
        var_data = self.global_variables.get(old_name)
        if new_type is not None:
            new_type = DataType(new_type).value

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
        final_type = DataType(var_data["type"]).value
        old_type = final_type
        type_changed = new_type is not None and new_type != old_type

        if type_changed:
            final_type = new_type

        # ===============================
        # 3. Tentukan value final
        # ===============================
        final_value = var_data["value"]

        if new_value is not None:
            if type_changed:
                final_value = self.get_default_value(final_type)
            else:
                if VariableManager.is_value_valid(final_type, {"value": new_value}):
                    final_value = new_value
        elif type_changed:
            final_value = self.get_default_value(final_type)
                        
        # Set data
        new_var = self.global_variables[final_name]
        new_var["type"] = DataType(final_type)
        new_var["value"] = final_value

        # ===============================
        # 4. Emit update
        # ===============================
        self.variable_updated.emit(old_name, final_name)
    
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

