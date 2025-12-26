from dataclasses import dataclass, field
from typing import Any, List, Optional, Dict

@dataclass
class Property:
    type: str
    value: Any
    options: Optional[List[Any]] = None                    # ENUM
    list_type: Optional['Property'] = None                 # LIST
    struct_fields: Optional[Dict[str, 'Property']] = None  # STRUCT
