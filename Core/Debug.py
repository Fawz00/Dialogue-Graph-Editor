import inspect
import sys
import datetime

from Core.Enums.LogLevel import LogLevel

class Debug:
    LEVELS = {
        'LOG': '\033[94m',      # Blue
        'WARNING': '\033[93m',  # Yellow
        'ERROR': '\033[91m',    # Red
        'ENDC': '\033[0m',      # Reset
    }

    log_data = []

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
        Debug.log_data.append({
            "timestamp": timestamp,
            "level": level.value,
            "message": message,
            "source": source
        })
        print(f"{color}[{timestamp}] [{level.value}] {message} ({source}){endc}", file=sys.stderr if level == LogLevel.ERROR else sys.stdout)

    @staticmethod
    def log(message):
        Debug._log(LogLevel.INFO, message)
    @staticmethod
    def log_warning(message):
        Debug._log(LogLevel.WARNING, message)

    @staticmethod
    def log_error(message):
        Debug._log(LogLevel.ERROR, message)
