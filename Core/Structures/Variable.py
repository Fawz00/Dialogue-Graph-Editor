from dataclasses import dataclass, field
from typing import Any, List, Optional, Dict
from uuid import uuid4
from Core.Enums.DataType import DataType

@dataclass
class Variable:
    type: DataType | None
    value: Any

    enabled: bool = True

    # Optional metadata for variable
    options: Optional[List[Any]] = None     # For ENUM types
    element_type: Optional[DataType] = None      # For ARRAY types
    class_id: Optional[str] = None          # For custom class/Object types

    display_name: Optional[str] = None      # Localization fallback
    localization_key: Optional[str] = None
    comment: Optional[str] = None
    placeholder: Optional[str] = None       # For STRING, UI display
    editable: bool = True                   # Can be edited in UI
    meta_editable: bool = True              # Can edit metadata in UI
    hints: Optional[Dict[str, Any]] = None  # Additional hints for UI or processing

    _id: str = field(default_factory=lambda: uuid4().hex, init=False, repr=False)

    @property
    def id(self) -> str:
        return self._id

# For future extensibility, not for now...

@dataclass
class TypeMetadata:
    options: Optional[List[Any]] = None
    element_type: Optional[DataType] = None
    class_id: Optional[str] = None

@dataclass
class UIMetadata:
    display_name: Optional[str] = None
    localization_key: Optional[str] = None
    comment: Optional[str] = None
    placeholder: Optional[str] = None
    hints: Optional[Dict[str, Any]] = None
    editable: bool = True
    meta_editable: bool = True