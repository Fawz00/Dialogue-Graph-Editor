from enum import Enum

class DataType(Enum):
    STRING = "string"
    INT = "int"
    FLOAT = "float"
    BOOL = "bool"
    ENUM = "enum"
    STRUCT = "struct"
    LIST = "list"
    CLASS = "class"