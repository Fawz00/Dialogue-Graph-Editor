from dataclasses import dataclass, field
from typing import Any, List, Optional, Dict
from uuid import uuid4
from Core.Enums.DataType import DataType

type StructType = dict[str, Variable]
type ArrayType = list[ValueType]
type ListType = list[Variable]
type ValueType = (
    StructType
    | ArrayType
    | ListType
    | list[StructType]
    | list[ArrayType]
    | list[ListType]
    | list[str]
    | list[int]
    | list[float]
    | list[bool]
    | str
    | int
    | float
    | bool
    | None
)

@dataclass
class Variable:
    type: DataType | None
    value: ValueType

    enabled: bool = True

    # Optional metadata for variable
    options: Optional[List[str]] = None     # For ENUM types
    element_type: Optional[DataType] = None # For ARRAY types
    class_id: Optional[str] = None          # For custom class/Object types
    struct_id: Optional[str] = None         # For custom struct types

    display_name: Optional[str] = None      # Localization fallback
    localization_key: Optional[str] = None
    comment: Optional[str] = None
    placeholder: Optional[str] = None       # For STRING, UI display
    editable: bool = True                   # Can be edited in UI
    hints: Optional[Dict[str, Any]] = None  # Additional hints for UI or processing

    _id: str = field(default_factory=lambda: uuid4().hex, init=False, repr=False)

    @property
    def id(self) -> str:
        return self._id

# For future extensibility, not for now...

@dataclass
class TypeMetadata:
    options: Optional[List[str]] = None
    element_type: Optional[DataType] = None
    class_id: Optional[str] = None
    struct_id: Optional[str] = None

@dataclass
class UIMetadata:
    display_name: Optional[str] = None
    localization_key: Optional[str] = None
    comment: Optional[str] = None
    placeholder: Optional[str] = None
    hints: Optional[Dict[str, Any]] = None
    editable: bool = True
