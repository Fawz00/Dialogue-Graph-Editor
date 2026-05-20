from dataclasses import dataclass
from inspect import FrameInfo
from typing import Optional
from Core.Enums.LogLevel import LogLevel

@dataclass
class LogData:
    sequence: int
    timestamp: str
    level: LogLevel
    message: str
    source: str
    traceback: Optional[list[FrameInfo]] = None