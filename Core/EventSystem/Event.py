from dataclasses import dataclass
from typing import Any, Dict
import time
import uuid

@dataclass(frozen=True)
class Event:
    type: str
    payload: Dict[str, Any]
    scope: str = "global"
    source: str | None = None
    timestamp: float = time.time()
    id: str = uuid.uuid4().hex
