from PyQt6.QtCore import QObject, pyqtSignal
from numpy import var

from Core.Debug import Debug
from Core.Enums.DataType import DataType
from Core.EventSystem.Event import Event
from Core.EventSystem.EventType import EventType
from Core.Structures.Variable import Variable

class VariableManager(QObject):
    # Konstanta untuk konfigurasi variabel
    _DEFAULT_VALUES = {
        DataType.STRING: "",
        DataType.INT: 0,
        DataType.FLOAT: 0.0,
        DataType.BOOL: False,
        DataType.STRUCT: {},
        DataType.ARRAY: [],
        DataType.LIST: [],
        DataType.ENUM: [],
        DataType.OBJECT: {}
    }

    SUPPORTED_TYPES_AS_STRING = [
        DataType.STRING.value,
        DataType.INT.value,
        DataType.FLOAT.value,
        DataType.BOOL.value,
        DataType.ARRAY.value,
        DataType.LIST.value,
    ]
    PRIMITIVE_TYPES_AS_STRING = [
        DataType.STRING.value,
        DataType.INT.value,
        DataType.FLOAT.value,
        DataType.BOOL.value
    ]

    def __init__(self, main_window=None):
        super().__init__(main_window)
        self._main_window = main_window

        # Inisialisasi dengan variabel placeholder
        self._global_variables: dict[str, Variable] = {
            "ThisIsEnum": Variable(
                type=DataType.ENUM,
                options=["Var1", "Var2", "Var3"],
                value="Var1"
            ),

            "ThisIsArray": Variable(
                type=DataType.ARRAY,
                element_type=DataType.INT,
                value=[1, 2, 3, 4, 5]
            ),

            "ThisIsList": Variable(
                type=DataType.LIST,
                value=[
                    Variable(type=DataType.STRING, value="Item1"),
                    Variable(type=DataType.FLOAT, value=2.5),
                    Variable(type=DataType.BOOL, value=True)
                ]
            ),

            "ThisIsAdvancedNested": Variable(
                type=DataType.STRUCT,
                value={
                    "Priority": Variable(type=DataType.INT, value=1),
                    "Interpolate": Variable(type=DataType.BOOL, value=False),
                    "Test Float": Variable(type=DataType.FLOAT, value=0.0),
                    "Text": Variable(type=DataType.STRING, value="None"),

                    "Example array": Variable(
                        type=DataType.ARRAY,
                        element_type=DataType.STRING,
                        value=["Item1", "Item2"]
                    ),

                    "Example list": Variable(
                        type=DataType.LIST,
                        value=[
                            Variable(type=DataType.INT, value=10),
                            Variable(type=DataType.FLOAT, value=3.14),
                            Variable(type=DataType.STRING, value="Hello")
                        ]
                    )
                }
            )
        }
    
    # === CRUD Methods ===
    
    def delete_global_variable(self, name):
        success = VariableManager.delete_variable(self._global_variables, name)

        if success:
            self._main_window.event_bus.publish(Event(
                type=EventType.EVENT_VARIABLE_REMOVED.value,
                source="VariableManager",
                payload={"name": name}
            ))
        
    
    @staticmethod
    def delete_variable(database, name) -> bool:
        if name in database:
            del database[name]
            return True
        return False
    
    def edit_global_variable(self, value_path: list, new_name: str = None, new_data: Variable = None):
        success = VariableManager.edit_variable(self._global_variables, value_path, new_name, new_data)

        if success:
            self._main_window.event_bus.publish(Event(
                type=EventType.EVENT_VARIABLE_UPDATED.value,
                source="VariableManager",
                payload={
                    "old_name": value_path[0],
                    "new_name": new_name or value_path[0]
                }
            ))
    
    @staticmethod
    def edit_variable(database, value_path: list, new_name: str = None, new_data: Variable = None) -> bool:
        def get_nested_meta(current_meta: Variable, path: list):
            parent = None
            key = None
            meta = current_meta

            for segment in path[1:]:
                parent = meta

                if DataType(meta.type) == DataType.STRUCT:
                    meta = meta.value.get(segment)
                    key = segment

                elif DataType(meta.type) == DataType.ARRAY:
                    try:
                        idx = int(segment)
                        meta = meta.value[idx]

                        key = idx
                    except (ValueError, IndexError):
                        Debug.log_error(f"Invalid list index '{segment}' while editing '{path}'.")
                        return None, None, None
                
                elif DataType(meta.type) == DataType.LIST:
                    try:
                        idx = int(segment)
                        meta = meta.value[idx]

                        key = idx
                    except (ValueError, IndexError):
                        Debug.log_error(f"Invalid list index '{segment}' while editing '{path}'.")
                        return None, None, None

                else:
                    Debug.log_error(f"Cannot traverse into type {meta.type} at '{segment}'.")
                    return None, None, None

                if meta is None:
                    Debug.log_error(f"Path '{path}' does not exist.")
                    return None, None, None

            return parent, key, meta

        # Edit variable berdasarkan path
        if not value_path:
            Debug.log_error("Value path is empty in edit_variable.")
            return False

        old_var_name = value_path[0]

        if old_var_name not in database:
            Debug.log_error(f"Variable '{old_var_name}' does not exist.")
            return False

        root_meta = database[old_var_name]
        parent: Variable | dict | list = None
        target_meta: Variable = None

        if len(value_path) == 1:
            key = old_var_name
            target_meta = root_meta
        else:
            parent, key, target_meta = get_nested_meta(root_meta, value_path)
            if target_meta is None:
                Debug.log_error(f"Failed to get target meta for path '{value_path}'.")
                return False

        # =========================
        # RENAME / REORDER
        # =========================
        if new_name is not None:

            if parent is None:
                # ROOT VARIABLE RENAME
                if new_name in database:
                    Debug.log_error(f"Variable '{new_name}' already exists.")
                    return False

                database[new_name] = database.pop(old_var_name)
                key = new_name

            # STRUCT
            elif isinstance(parent, dict):
                if new_name in parent:
                    Debug.log_error(f"Variable '{new_name}' already exists.")
                    return False
                parent[new_name] = parent.pop(key)
                key = new_name

            # LIST reorder
            elif isinstance(parent, list):
                try:
                    new_index = int(new_name)
                except ValueError:
                    Debug.log_error("List reorder requires integer index.")
                    return False

                old_index = key
                list_len = len(parent)

                if not (0 <= new_index < list_len):
                    Debug.log_error(f"Index {new_index} out of range for list reorder.")
                    return False

                if new_index != old_index:
                    item = parent.pop(old_index)
                    parent.insert(new_index, item)
                    key = new_index

            else:
                Debug.log_error(f"Invalid parent type ({type(parent)}) for rename/reorder.")
                return False

        # =========================
        # CHANGE VALUE
        # =========================
        if new_data.value is not None:
            if parent is not None and DataType(parent.type) == DataType.ARRAY:
                old_value = target_meta

                # Coba pasang dulu
                parent.value[key] = new_data.value

                # Validasi
                if not VariableManager.is_value_valid(new_data, parent.element_type):
                    # Rollback jika invalid
                    parent.value[key] = old_value
                    Debug.log_warning(f"Invalid array element value '{new_data.value}' for type {parent.element_type}.")
            else:
                old_value = target_meta.value

                # Coba pasang dulu
                target_meta.value = new_data.value

                # Validasi
                if not VariableManager.is_value_valid(target_meta):
                    # Rollback jika invalid
                    target_meta.value = old_value

                    Debug.log_warning(f"Invalid value '{target_meta.value}' for type {target_meta.type}.")

                    # Cek apakah value lama valid, kalau tidak set ke default
                    if not VariableManager.is_value_valid(target_meta):
                        VariableManager.reset_to_default_value(target_meta)
        
        # =========================
        # CHANGE OTHER PROPS
        # =========================
        # Options
        if new_data.options is not None:
            target_meta.options = new_data.options
        elif isinstance(target_meta, Variable):
            if DataType(target_meta.type) != DataType.ENUM:
                target_meta.options = None
        
        # Element Type
        if new_data.element_type is not None:
            target_meta.element_type = new_data.element_type
        elif isinstance(target_meta, Variable):
            if DataType(target_meta.type) != DataType.ARRAY:
                target_meta.element_type = None

        # =========================
        # CHANGE TYPE
        # =========================
        if new_data.type is not None:
            target_meta.type = new_data.type

            # Bersihkan metadata lama
            target_meta.options = None
            target_meta.element_type = None

            # Inisialisasi metadata sesuai tipe
            if new_data.type == DataType.ENUM.value:
                target_meta.options = []
            elif new_data.type == DataType.ARRAY.value:
                target_meta.element_type = DataType.STRING.value
            elif new_data.type == DataType.STRUCT.value:
                pass  # STRUCT hanya butuh value dict

            # Value selalu reset dari sumber kebenaran
            VariableManager.convert_variable_to_type(target_meta, new_data.type)

        return True
    
    def create_global_variable(self, name, var_type, value=None):
        success = VariableManager.create_variable(self._global_variables, name, var_type, value)

        if success:
            self._main_window.event_bus.publish(Event(
                type=EventType.EVENT_VARIABLE_ADDED.value,
                source="VariableManager",
                payload={"name": name}
            ))

    @staticmethod
    def create_variable(database, name, var_type, value=None) -> bool:
        if name in database:
            return False  # Sudah ada
        
        database[name] = Variable(
            type=DataType(var_type),
            value=VariableManager.get_default_value(var_type) if value is None else value
        )

        if value is not None:
            database[name].value = value
        
        return True
    
    def get_global_variable(self, name):
        return self._global_variables.get(name, None)

    def get_all_global_variables(self):
        return self._global_variables



    # ===== Helper Methods =====
    #region Helper Methods

    @staticmethod
    def get_default_value(var_type: str | DataType):
        """Mengembalikan nilai default berdasarkan tipe data"""
        dt = DataType(var_type)
        result = VariableManager._DEFAULT_VALUES.get(dt, None)
        return result

    @staticmethod
    def reset_to_default_value(var: Variable):
        if var is None:
            Debug.log_error("Cannot reset to default value: Variable is None.")
            return
        
        if DataType(var.type) is DataType.ENUM:
            if var.options and len(var.options) > 0:
                options_list = list(var.options)
                var.value = options_list[0]
            else:
                var.value = ""
                Debug.log_warning("ENUM variable has no options to set default value.")
            return
        else:
            var.value = VariableManager.get_default_value(var.type)

    @staticmethod
    def convert_variable_to_type(var: Variable, dtype: str | DataType):
        """
        Mengonversi nilai ke tipe data tertentu.
        Mengembalikan nilai yang dikonversi atau None jika gagal.
        """
        if var is None:
            Debug.log_error("Cannot convert variable: Variable is None.")
            return

        try:
            # ===============================
            # NORMALISASI TYPE
            # ===============================
            if isinstance(dtype, str):
                dtype = DataType(dtype)
            
            if var.type != dtype:
                var.type = dtype.value

            # ===============================
            # PRIMITIVE TYPES
            # ===============================
            if dtype == DataType.STRING:
                var.value = str(var.value)
                return

            if dtype == DataType.INT:
                var.value = int(var.value)
                return

            if dtype == DataType.FLOAT:
                var.value = float(var.value)
                return

            if dtype == DataType.BOOL:
                if isinstance(var.value, str):
                    val_lower = var.value.lower()
                    if val_lower in ["true", "1", "yes"]:
                        var.value = True
                    else:
                        var.value = False
                var.value = bool(var.value)
                return
            
        except Exception:
            VariableManager.reset_to_default_value(var)
        
        VariableManager.reset_to_default_value(var)

    @staticmethod
    def is_value_valid(meta: Variable, dtype: DataType|str = None) -> bool:
        """
        Mengecek apakah value valid untuk DataType tertentu
        berdasarkan metadata variabel.
        """

        try:
            # ===============================
            # NORMALISASI TYPE
            # ===============================
            if dtype is None:
                dtype = meta.type

            dtype = DataType(dtype)

            value = meta.value

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
                options = meta.options
                return isinstance(options, list) and value in options

            # ===============================
            # ARRAY
            # ===============================
            if dtype == DataType.ARRAY:
                if not isinstance(value, list):
                    return False
                
                if not meta.element_type:
                    return False

                for item in value:
                    if not VariableManager.is_value_valid(Variable(value=item, type=meta.element_type)):
                        return False
                return True

            # ===============================
            # LIST
            # ===============================
            if dtype == DataType.LIST:
                if not isinstance(value, list):
                    return False

                for item in value:
                    if not VariableManager.is_value_valid(item):
                        return False
                return True

            # ===============================
            # STRUCT
            # ===============================
            if dtype == DataType.STRUCT:
                if not isinstance(value, dict):
                    return False

                structure = meta.structure
                if not structure:
                    return True

                for key, field_meta in structure.items():
                    if key not in value:
                        return False

                    field_type = field_meta.get("type")
                    field_value = value[key]

                    if not VariableManager.is_value_valid(Variable(value=field_value, type=field_type)):
                        return False
                return True

            # ===============================
            # OBJECT
            # ===============================
            if dtype == DataType.OBJECT:
                class_name = meta.class_name
                if not class_name:
                    return False

                if isinstance(value, str):
                    return True

                return value.__class__.__name__ == class_name

        except Exception:
            return False

        return False

    #endregion Helper Methods
