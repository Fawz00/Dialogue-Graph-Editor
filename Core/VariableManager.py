from __future__ import annotations
from typing import TYPE_CHECKING, cast

from typing import Any

from PyQt6.QtCore import QObject

from Core.Debug.Debug import Debug
from Core.Enums.DataType import DataType
from Core.EventSystem.Event import Event
from Core.EventSystem.EventType import EventType
from Core.Structures.Variable import ArrayType, ListType, StructType, ValueType, Variable

if TYPE_CHECKING:
    from Main import MainWindow

class VariableManager(QObject):
    # Konstanta untuk konfigurasi variabel
    _DEFAULT_VALUES: dict[DataType, Any] = {
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

    def __init__(self, main_window: MainWindow):
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
                    ),
                    "AnotherNested": Variable(
                        type=DataType.STRUCT,
                        value={
                            "Into": Variable(type=DataType.INT, value=1),
                            "booru": Variable(type=DataType.BOOL, value=False),
                            "Sutorin": Variable(type=DataType.STRING, value="None"),

                            "Golden Array": Variable(
                                type=DataType.ARRAY,
                                element_type=DataType.STRING,
                                value=["Crimsom Agate", "Deluxe Ignite", "Guenuss Abilitus"]
                            ),

                            "The Great List": Variable(
                                type=DataType.LIST,
                                value=[
                                    Variable(type=DataType.INT, value=4294967296),
                                    Variable(type=DataType.FLOAT, value=3.14159265358979),
                                    Variable(type=DataType.STRING, value="こんにちは"),
                                    Variable(
                                        type=DataType.STRUCT,
                                        value={
                                            "Into": Variable(type=DataType.INT, value=1),
                                            "booru": Variable(type=DataType.BOOL, value=False),
                                            "Sutorin": Variable(type=DataType.STRING, value="None"),
                                        }
                                    )
                                ]
                            )
                        }
                    )
                }
            )
        }
    
    # === CRUD Methods ===
    
    def delete_global_variable(self, name: str):
        success = VariableManager.delete_variable(self._global_variables, name)

        if success:
            self._main_window.event_bus.publish(Event(
                type=EventType.EVENT_VARIABLE_REMOVED.value,
                source="VariableManager",
                payload={"name": name}
            ))
        
    
    @staticmethod
    def delete_variable(database: dict[str, Variable], name: str) -> bool:
        if name in database:
            del database[name]
            return True
        return False
    
    def edit_global_variable(self, value_path: list[str], new_name: str | None = None, new_data: Variable | None = None):
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
    def edit_variable(database: dict[str, Variable], value_path: list[str], new_name: str | None = None, new_data: Variable | None = None) -> bool:
        def get_nested_var(path: list[str] = value_path) -> tuple[Variable | None, str | int | None, Variable | ValueType | None]: # parent, key, child
            if not path:
                Debug.log_error("Value path is empty in get_nested_var.")
                return None, None, None
            if path[0] not in database:
                Debug.log_error(f"Variable '{path[0]}' does not exist in get_nested_var.")
                return None, None, None
            
            parent: Variable | None = None
            key: str | int | None = None
            child: Variable | ValueType | None = database.get(path[0], None)

            for segment in path[1:]:
                parent = child if isinstance(child, Variable) else None

                if parent is None:
                    Debug.log_error(f"Path '{path}' does not exist.")
                    return None, None, None

                if DataType(parent.type) == DataType.STRUCT:
                    value = cast(StructType, parent.value)
                    child = value.get(segment, None)
                    if not child:
                        Debug.log_warning(f"Key '{segment}' not found in STRUCT at '{path}'.")
                    key = segment

                elif DataType(parent.type) == DataType.ARRAY:
                    try:
                        idx = int(segment)
                        value = cast(ArrayType, parent.value)
                        child = value[idx]
                        key = idx

                    except (ValueError, IndexError):
                        Debug.log_error(f"Invalid array index '{segment}' while editing '{path}'.")
                        return None, None, None
                
                elif DataType(parent.type) == DataType.LIST:
                    try:
                        idx = int(segment)
                        value = cast(ListType, parent.value)
                        child = value[idx]
                        key = idx

                    except (ValueError, IndexError):
                        Debug.log_error(f"Invalid list index '{segment}' while editing '{path}'.")
                        return None, None, None

                else:
                    Debug.log_error(f"Cannot traverse into type {parent.type} at '{segment}'.")
                    return None, None, None

            return parent, key, child

        # Edit variable berdasarkan path
        if not value_path:
            Debug.log_error("Value path is empty in edit_variable.")
            return False

        old_var_name = value_path[0]

        if old_var_name not in database:
            Debug.log_error(f"Variable '{old_var_name}' does not exist.")
            return False

        parent, key, child = get_nested_var(value_path)

        if child is None:
            Debug.log_error(f"Failed to get child for path '{value_path}'.")
            return False

        # =========================
        # RENAME ROOT
        # =========================
        if new_name is not None:

            if parent is None:
                # ROOT VARIABLE RENAME
                if new_name in database:
                    Debug.log_error(f"Variable '{new_name}' already exists.")
                    return False

                database[new_name] = database.pop(old_var_name)
                key = new_name

        # =========================
        # CHANGE VALUE
        # =========================
        if new_data is not None:
            if new_data.value is not None:
                if parent is not None:

                    # ARRAY element change
                    # parent = the array itself (Variable)
                    # key = index in array (int)
                    # child = value at that index (ValueType)
                    if parent.type == DataType.ARRAY:
                        array_value = cast(ArrayType, parent.value)
                        old_value = cast(ValueType, child)

                        try:
                            key = int(key) if key is not None else -1
                        except ValueError:
                            Debug.log_error("Invalid array index for value change.")
                            return False

                        # Coba pasang dulu
                        array_value[key] = new_data.value

                        # Validasi
                        if not VariableManager.is_value_valid(new_data, DataType(parent.element_type)):
                            # Rollback jika invalid
                            array_value[key] = old_value
                            Debug.log_warning(f"Invalid array element value '{new_data.value}' for type {parent.element_type}.")
                
                    # List element tidak perlu validasi parent karena List bisa menampung berbagai tipe, validasi langsung pada elementnya saja
                
                # Tipe primitif tidak harus validasi parent
                # PRIMITIVE
                target_var = cast(Variable, child)
                old_val = target_var.value

                # Coba pasang dulu
                target_var.value = new_data.value

                # Validasi
                if not VariableManager.is_value_valid(target_var):
                    # Rollback jika invalid
                    target_var.value = old_val

                    Debug.log_warning(f"Invalid value '{target_var.value}' for type {target_var.type}.")

                    # Cek apakah value lama valid, kalau tidak set ke default
                    if not VariableManager.is_value_valid(target_var):
                        VariableManager.reset_to_default_value(target_var)

            # =========================
            # CHANGE OTHER PROPS
            # =========================
            # Options
            if isinstance(parent, Variable):
                if new_data.options:
                    parent.options = new_data.options
                elif DataType(parent.type) != DataType.ENUM:
                    parent.options = None
        
            # Element Type
            if isinstance(parent, Variable):
                if new_data.element_type is not None:
                    parent.element_type = new_data.element_type
                elif DataType(parent.type) != DataType.ARRAY:
                    parent.element_type = None

            # =========================
            # CHANGE TYPE
            # =========================
            if new_data.type is not None:
                if parent is not None and parent.type is (DataType.ARRAY or DataType.LIST) and new_data.type == parent.type:
                    return True  # Tidak perlu ubah tipe jika sama

                if isinstance(child, Variable):
                    child.type = new_data.type

                    # Bersihkan metadata lama
                    child.options = None
                    child.element_type = None

                    # Inisialisasi metadata sesuai tipe
                    if new_data.type == DataType.ENUM:
                        child.options = []
                    elif new_data.type == DataType.ARRAY:
                        child.element_type = DataType.STRING
                    elif new_data.type == DataType.STRUCT:
                        pass  # STRUCT hanya butuh value dict

                    # Value selalu reset dari sumber kebenaran
                    VariableManager.convert_variable_to_type(child, new_data.type)
                else:
                    Debug.log_error("Attempting to change type of a non-variable child, which is not supported.")
                    return False

        return True
    
    def create_global_variable(self, name: str, var_type: DataType, value: Any | None = None):
        success = VariableManager.create_variable(self._global_variables, name, var_type, value)

        if success:
            self._main_window.event_bus.publish(Event(
                type=EventType.EVENT_VARIABLE_ADDED.value,
                source="VariableManager",
                payload={"name": name}
            ))

    @staticmethod
    def create_variable(database: dict[str, Variable], name: str, var_type: DataType, value: Any | None = None) -> bool:
        if name in database:
            return False  # Sudah ada
        
        database[name] = Variable(
            type=DataType(var_type),
            value=VariableManager.get_default_value(var_type) if value is None else value
        )

        if value is not None:
            database[name].value = value
        
        return True
    
    def get_global_variable(self, name: str) -> Variable | None:
        return self._global_variables.get(name, None)

    def get_all_global_variables(self):
        return self._global_variables



    # ===== Helper Methods =====
    #region Helper Methods

    @staticmethod
    def get_default_value(var_type: DataType) -> Any:
        """Mengembalikan nilai default berdasarkan tipe data"""
        dt = DataType(var_type)
        result = VariableManager._DEFAULT_VALUES.get(dt, None)
        return result

    @staticmethod
    def reset_to_default_value(var: Variable):
        if DataType(var.type) is DataType.ENUM:
            if var.options and len(var.options) > 0:
                options_list = list(var.options)
                var.value = options_list[0]
            else:
                var.value = ""
                Debug.log_warning("ENUM variable has no options to set default value.")
            return
        else:
            if var.type is not None:
                var.value = VariableManager.get_default_value(var.type)
            else:
                Debug.log_warning("Variable type is None, cannot reset to default value.")
    
    @staticmethod
    def try_to_assign_value(var: Variable, new_value: ValueType) -> bool:
        """Mencoba mengonversi dan menetapkan nilai baru ke variabel. Mengembalikan True jika berhasil."""
        try:
            if var.type is None:
                Debug.log_warning("Variable type is None, cannot assign value.")
                return False

            converted_value = VariableManager.convert_variable_to_type(Variable(value=new_value, type=var.type), var.type)
            if VariableManager.is_value_valid(Variable(value=converted_value, type=var.type), var.type):
                var.value = converted_value
                return True
            else:
                Debug.log_warning(f"Value '{new_value}' is not valid for type {var.type}.")
                return False
        except Exception as e:
            Debug.log_error(f"Error converting value '{new_value}' to type {var.type}: {e}")
            return False

    @staticmethod
    def convert_variable_to_type(var: Variable, dtype: DataType):
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
            
            if var.type != dtype:
                var.type = dtype
            
            if var.value is None:
                var.value = VariableManager.get_default_value(dtype)
                return
        
            # ===============================
            # PRIMITIVE TYPES
            # ===============================
            if dtype == DataType.STRING:
                var.value = str(var.value)
                return

            if dtype == DataType.INT:
                if isinstance(var.value, (str, int, float, bool)):
                    var.value = int(var.value)
                return

            if dtype == DataType.FLOAT:
                if isinstance(var.value, (str, int, float, bool)):
                    var.value = float(var.value)
                return

            if dtype == DataType.BOOL:
                if isinstance(var.value, (str, int, float, bool)):
                    if isinstance(var.value, str):
                        val_lower = var.value.lower()
                        if val_lower in ["true", "1", "yes"]:
                            var.value = True
                        else:
                            var.value = False
                    else:
                        var.value = bool(var.value)
                return
            
        except Exception:
            VariableManager.reset_to_default_value(var)
        
        VariableManager.reset_to_default_value(var)

    @staticmethod
    def is_value_valid(meta: Variable, dtype: DataType | None = None) -> bool:
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
                return isinstance(value, str)

            if dtype == DataType.INT:
                return isinstance(value, int) and not isinstance(value, bool)  # bool turunan dari int, harus dikecualikan

            if dtype == DataType.FLOAT:
                return isinstance(value, float)  # float adalah tipe data dasar

            if dtype == DataType.BOOL:
                return isinstance(value, bool)

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
                    if not isinstance(item, Variable):
                        if not VariableManager.is_value_valid(Variable(value=item, type=meta.element_type)):
                            return False
                    else:
                        if not VariableManager.is_value_valid(item):
                            return False
                return True

            # ===============================
            # LIST
            # ===============================
            if dtype == DataType.LIST:
                if not isinstance(value, list):
                    return False

                for item in value:
                    if not isinstance(item, Variable):
                        if not VariableManager.is_value_valid(Variable(value=item, type=meta.element_type)):
                            return False
                    else:
                        if not VariableManager.is_value_valid(item):
                            return False
                return True

            # ===============================
            # STRUCT
            # ===============================
            # NOT IMPLEMENTED: STRUCT validation requires schema definition which is not implemented yet.
            if dtype == DataType.STRUCT:
                if not isinstance(value, dict):
                    return False

                structure = meta.structure # type: ignore
                if not structure:
                    return True

                for key, field_meta in structure.items(): # type: ignore
                    if key not in value:
                        return False

                    field_type = field_meta.get("type") # type: ignore
                    field_value = value[key]

                    if not VariableManager.is_value_valid(Variable(value=field_value, type=field_type)): # type: ignore
                        return False
                return True

            # ===============================
            # OBJECT
            # ===============================
            # NOT IMPLEMENTED: OBJECT validation requires class definition which is not implemented yet.
            if dtype == DataType.OBJECT:
                class_name = meta.class_name # type: ignore
                if not class_name:
                    return False

                if isinstance(value, str):
                    return True

                return value.__class__.__name__ == class_name # type: ignore

        except Exception:
            return False

        return False

    #endregion Helper Methods
