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
    
    def get_default_value(self, var_type, type_name=None):
        """Mengembalikan nilai default berdasarkan tipe data"""
        dt = DataType(var_type)
        if dt == DataType.LIST and type_name:
            # Jika list dengan tipe tertentu, kembalikan list kosong
            return []
        return VariableManager.DEFAULT_VALUES.get(dt, None)
    
    # === CRUD Methods ===
    
    def delete_variable(self, name):
        if name in self.global_variables:
            del self.global_variables[name]
            self.variable_deleted.emit(name)
    
    def edit_variable(self, old_name, new_name=None, new_type=None, new_value=None):
        if old_name not in self.global_variables:
            return

        var_data = self.global_variables[old_name]

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
        if new_type and new_type != var_data["type"]:
            final_type = new_type
            var_data["type"] = final_type

        # ===============================
        # 3. Tentukan value final
        # ===============================
        if new_value is not None:
            val_str = str(new_value)
            try:
                dt = DataType(final_type)
                if dt == DataType.INT:
                    var_data["value"] = int(float(val_str))
                elif dt == DataType.FLOAT:
                    var_data["value"] = float(val_str)
                elif dt == DataType.BOOL:
                    var_data["value"] = val_str.lower() in ("1", "true", "yes", "t", "y")
                elif dt == DataType.STRING:
                    var_data["value"] = val_str
                else:
                    var_data["value"] = new_value
            except Exception:
                pass  # gagal konversi → value lama dipertahankan
        else:
            # Jika tipe berubah tapi value tidak diberikan → reset default
            if final_type != var_data["type"]:
                var_data["value"] = VariableManager.DEFAULT_VALUES[DataType(final_type)]
        
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