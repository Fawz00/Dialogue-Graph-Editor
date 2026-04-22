from enum import Enum

class DataType(Enum):
    STRING = "string"
    INT = "integer"
    FLOAT = "float"
    BOOL = "boolean"
    ENUM = "enumeration"
    STRUCT = "structure"
    ARRAY = "array"
    LIST = "list"
    OBJECT = "object"