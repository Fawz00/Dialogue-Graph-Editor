from dataclasses import dataclass, field
from typing import Any, List, Optional, Dict
from uuid import uuid4
from Core.Enums.DataType import DataType

@dataclass
class Variable:
    type: str
    value: Any

    # Optional metadata for variable
    options: Optional[List[Any]] = None     # For ENUM types
    element_type: Optional[str] = None      # For ARRAY types
    class_id: Optional[str] = None          # For custom class/Object types

    display_name: Optional[str] = None      # Localization fallback
    localization_key: Optional[str] = None
    comment: Optional[str] = None
    placeholder: Optional[str] = None       # For STRING, UI display

    _id: str = field(default_factory=lambda: uuid4().hex, init=False, repr=False)

    @property
    def id(self) -> str:
        return self._id

# For future extensibility, not for now...

@dataclass
class TypeMetadata:
    element_type: Optional["DataType"] = None
    class_id: Optional[str] = None

@dataclass
class UIMetadata:
    display_name: Optional[str] = None
    localization_key: Optional[str] = None
    comment: Optional[str] = None
    placeholder: Optional[str] = None
    options: Optional[List[Any]] = None
    hints: Optional[Dict[str, Any]] = None
