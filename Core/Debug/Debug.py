from __future__ import annotations
from typing import TYPE_CHECKING

import inspect
import sys
import datetime
import threading
import itertools

from Core.Debug.LogData import LogData
from Core.Enums.LogLevel import LogLevel
from Core.EventSystem.Event import Event
from Core.EventSystem.EventType import EventType

if TYPE_CHECKING:
    from Main import MainWindow

class Debug:
    LEVELS = {
        'DEBUG': '\033[90m',    # Grey
        'INFO': '\033[94m',     # Blue
        'WARNING': '\033[93m',  # Yellow
        'ERROR': '\033[91m',    # Red
        'CRITICAL': '\033[95m', # Magenta
        'ENDC': '\033[0m',      # Reset
    }
    MAX_LOG_ENTRIES = 2048  # Limit log entries to prevent memory bloat

    _main_window: MainWindow | None = None
    log_data: list[LogData] = []
    _log_lock = threading.RLock()
    _sequence_counter = itertools.count()

    @classmethod
    def set_main_window(cls, main_window: MainWindow):
        cls._main_window = main_window

    @staticmethod
    def _get_caller_info():
        frame = inspect.currentframe()
        if frame is None:
            return "Unknown Source"

        frame = frame.f_back

        while frame:
            # Ambil modul dari frame ini
            module = inspect.getmodule(frame)
            if module:
                # Jika modul bukan Debug sendiri, return info ini
                if module.__name__ != __name__:
                    filename = frame.f_code.co_filename
                    lineno = frame.f_lineno
                    func = frame.f_code.co_name
                    return f"{filename}:{lineno} in {func}()"
            frame = frame.f_back

        return "Unknown Source"

    @staticmethod
    def _log(level: LogLevel, message: str):
        with Debug._log_lock:
            color = Debug.LEVELS.get(level.name, '')
            endc = Debug.LEVELS['ENDC']

            timestamp = datetime.datetime.now().strftime(
                '%Y-%m-%d %H:%M:%S.%f'
            )[:-3]

            source = Debug._get_caller_info()
            traceback = inspect.stack()

            data = LogData(
                sequence=next(Debug._sequence_counter),
                timestamp=timestamp,
                level=level,
                message=message,
                source=source,
                traceback=traceback
            )

            Debug.log_data.append(data)

            if len(Debug.log_data) > Debug.MAX_LOG_ENTRIES:
                Debug.log_data.pop(0)

            if Debug._main_window:
                Debug._main_window.event_bus.publish(Event(
                    type=EventType.EVENT_LOG_ADDED.value,
                    source=source,
                    payload={
                        "data": data
                    }
                ))

            print(
                f"{color}[{timestamp}] "
                f"[{level.value}] "
                f"{message} ({source}){endc}",
                file=sys.stderr if level == LogLevel.ERROR else sys.stdout,
                flush=True
            )

            if level in (LogLevel.ERROR, LogLevel.WARNING):
                print(
                    "Traceback (most recent call last):",
                    file=sys.stderr,
                    flush=True
                )

                for frame in traceback[1:]:
                    filename = frame.filename
                    lineno = frame.lineno
                    func = frame.function

                    print(
                        f'  File "{filename}", line {lineno}, in {func}',
                        file=sys.stderr,
                        flush=True
                    )

    @staticmethod
    def log(message: str):
        Debug._log(LogLevel.INFO, message)
    @staticmethod
    def log_debug(message: str):
        Debug._log(LogLevel.DEBUG, message)
    @staticmethod
    def log_warning(message: str):
        Debug._log(LogLevel.WARNING, message)
    @staticmethod
    def log_error(message: str):
        Debug._log(LogLevel.ERROR, message)
    @staticmethod
    def log_critical(message: str):
        Debug._log(LogLevel.CRITICAL, message)
