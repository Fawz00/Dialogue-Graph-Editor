from enum import Enum

class DataType(Enum):
    STRING = "string"
    INT = "integer"
    FLOAT = "float"
    BOOL = "boolean"
    ENUM = "enummeration"
    STRUCT = "structure"
    LIST = "list"
    CLASS = "class"