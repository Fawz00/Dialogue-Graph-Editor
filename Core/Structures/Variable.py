from dataclasses import dataclass, field
from typing import Any, List, Optional, Dict

@dataclass
class Variable:
    type: str
    value: Any

    # Optional metadata for variable
    display_name: Optional[str] = None
    options: Optional[List[Any]] = None
    element_type: Optional[str] = None
