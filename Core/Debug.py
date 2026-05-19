import inspect
import sys
import datetime

from Core.Enums.LogLevel import LogLevel
from Core.EventSystem.Event import Event
from Core.EventSystem.EventType import EventType

class Debug:
    LEVELS = {
        'DEBUG': '\033[90m',    # Grey
        'INFO': '\033[94m',     # Blue
        'WARNING': '\033[93m',  # Yellow
        'ERROR': '\033[91m',    # Red
        'CRITICAL': '\033[95m', # Magenta
        'ENDC': '\033[0m',      # Reset
    }
    MAX_LOG_ENTRIES = 1048576  # Limit log entries to prevent memory bloat

    _main_window = None
    log_data = []

    @classmethod
    def set_main_window(cls, main_window):
        cls._main_window = main_window

    @staticmethod
    def _get_caller_info():
        frame = inspect.currentframe()
        # Lompat dari frame _get_caller_info ke frame sebelumnya
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
        color = Debug.LEVELS.get(level, '')
        endc = Debug.LEVELS['ENDC']
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        source = Debug._get_caller_info()
        traceback = inspect.stack()

        data = {
            "timestamp": timestamp,
            "level": level.value,
            "message": message,
            "source": source,
            "traceback": traceback
        }

        Debug.log_data.append(data)
        
        # Limit the number of log entries
        if len(Debug.log_data) > Debug.MAX_LOG_ENTRIES:
            Debug.log_data.pop(0)

        if Debug._main_window:
            Debug._main_window.event_bus.publish(Event(
                type=EventType.EVENT_LOG_ADDED.value,
                source=source,
                payload=data
            ))

        print(f"{color}[{timestamp}] [{level.value}] {message} ({source}){endc}", file=sys.stderr if level == LogLevel.ERROR else sys.stdout)

        if level == LogLevel.ERROR or level == LogLevel.WARNING:
            print("Traceback (most recent call last):", file=sys.stderr)
            for frame in traceback[1:]:  # Skip frame _log itu sendiri
                filename = frame.filename
                lineno = frame.lineno
                func = frame.function
                print(f'  File "{filename}", line {lineno}, in {func}', file=sys.stderr)

    @staticmethod
    def log(message):
        Debug._log(LogLevel.INFO, message)
    @staticmethod
    def log_debug(message):
        Debug._log(LogLevel.DEBUG, message)
    @staticmethod
    def log_warning(message):
        Debug._log(LogLevel.WARNING, message)
    @staticmethod
    def log_error(message):
        Debug._log(LogLevel.ERROR, message)
    @staticmethod
    def log_critical(message):
        Debug._log(LogLevel.CRITICAL, message)
