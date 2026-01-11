from PyQt6.QtCore import QObject, pyqtSignal

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

    SUPPORTED_TYPES_AS_STRING = list(dt.value for dt in _DEFAULT_VALUES.keys())

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
    
    def delete_variable(self, name):
        if name in self._global_variables:
            del self._global_variables[name]
            self._main_window.event_bus.publish(Event(
                type=EventType.EVENT_VARIABLE_REMOVED.value,
                source="VariableManager",
                payload={"name": name}
            ))
    
    def edit_variable(self, value_path: list, new_name: str = None, new_data: Variable = None):
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
            return

        old_var_name = value_path[0]

        if old_var_name not in self._global_variables:
            Debug.log_error(f"Variable '{old_var_name}' does not exist.")
            return

        root_meta = self._global_variables[old_var_name]
        parent: Variable | dict | list = None
        target_meta: Variable = None

        if len(value_path) == 1:
            key = old_var_name
            target_meta = root_meta
        else:
            parent, key, target_meta = get_nested_meta(root_meta, value_path)
            if target_meta is None:
                return

        # =========================
        # RENAME / REORDER
        # =========================
        if new_name is not None:

            if parent is None:
                # ROOT VARIABLE RENAME
                if new_name in self._global_variables:
                    Debug.log_error(f"Variable '{new_name}' already exists.")
                    return

                self._global_variables[new_name] = self._global_variables.pop(old_var_name)
                key = new_name

            # STRUCT
            elif isinstance(parent, dict):
                if new_name in parent:
                    Debug.log_error(f"Variable '{new_name}' already exists.")
                    return
                parent[new_name] = parent.pop(key)
                key = new_name

            # LIST reorder
            elif isinstance(parent, list):
                try:
                    new_index = int(new_name)
                except ValueError:
                    Debug.log_error("List reorder requires integer index.")
                    return

                old_index = key
                list_len = len(parent)

                if not (0 <= new_index < list_len):
                    Debug.log_error(f"Index {new_index} out of range for list reorder.")
                    return

                if new_index != old_index:
                    item = parent.pop(old_index)
                    parent.insert(new_index, item)
                    key = new_index

            else:
                Debug.log_error(f"Invalid parent type ({type(parent)}) for rename/reorder.")
                return

        # =========================
        # CHANGE VALUE
        # =========================
        if new_data.value is not None:
            if parent is not None and DataType(parent.type) == DataType.ARRAY:
                old_value = target_meta

                # Coba pasang dulu
                parent.value[key] = new_data.value

                # Validasi
                if not self.is_value_valid(parent.element_type, new_data):
                    # Rollback jika invalid
                    parent.value[key] = old_value
                    Debug.log_warning(f"Invalid array element value '{new_data.value}' for type {parent.element_type}.")
            else:
                old_value = target_meta.value

                # Coba pasang dulu
                target_meta.value = new_data.value

                # Validasi
                if not self.is_value_valid(target_meta.type, target_meta):
                    # Rollback jika invalid
                    target_meta.value = old_value
                    Debug.log_warning(f"Invalid value '{new_data.value}' for type {target_meta.type}.")
        
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
            target_meta.value = VariableManager.convert_value_to_type(target_meta.value, new_data.type)

        # =========================
        # EMIT EVENT
        # =========================
        self._main_window.event_bus.publish(Event(
            type=EventType.EVENT_VARIABLE_UPDATED.value,
            source="VariableManager",
            payload={
                "old_name": old_var_name,
                "new_name": new_name or old_var_name
            }
        ))
    
    def create_variable(self, name, var_type, value=None):
        if name in self._global_variables:
            return  # Sudah ada
        
        self._global_variables[name] = Variable(
            type=DataType(var_type),
            value=VariableManager.get_default_value(var_type) if value is None else value
        )

        if value is not None:
            self._global_variables[name].value = value

        self._main_window.event_bus.publish(Event(
            type=EventType.EVENT_VARIABLE_ADDED.value,
            source="VariableManager",
            payload={"name": name}
        ))
    
    def get_variable(self, name):
        return self._global_variables.get(name, None)

    def get_all_variables(self):
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
    def convert_value_to_type(value, dtype: str | DataType):
        """
        Mengonversi nilai ke tipe data tertentu.
        Mengembalikan nilai yang dikonversi atau None jika gagal.
        """

        try:
            # ===============================
            # NORMALISASI TYPE
            # ===============================
            if isinstance(dtype, str):
                dtype = DataType(dtype)

            # ===============================
            # PRIMITIVE TYPES
            # ===============================
            if dtype == DataType.STRING:
                return str(value)

            if dtype == DataType.INT:
                return int(value)

            if dtype == DataType.FLOAT:
                return float(value)

            if dtype == DataType.BOOL:
                if isinstance(value, str):
                    val_lower = value.lower()
                    if val_lower in ["true", "1", "yes"]:
                        return True
                    else:
                        return False
                return bool(value)

        except Exception:
            return VariableManager.get_default_value(dtype)

        return VariableManager.get_default_value(dtype)
    
    @staticmethod
    def is_value_valid(dtype, meta: Variable) -> bool:
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

                element_type = meta.element_type
                if not element_type:
                    return True

                for item in value:
                    if not VariableManager.is_value_valid(element_type, Variable(value=item)):
                        return False
                return True

            # ===============================
            # LIST
            # ===============================
            if dtype == DataType.LIST:
                if not isinstance(value, list):
                    return False

                for item in value:
                    if not VariableManager.is_value_valid(element_type, Variable(value=item)):
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

                    if not VariableManager.is_value_valid(field_type, Variable(value=field_value)):
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
