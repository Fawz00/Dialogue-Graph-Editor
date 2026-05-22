from __future__ import annotations

import atexit
import datetime
import inspect
import itertools
import os
import sys
import threading
import traceback

from collections import deque
from typing import TYPE_CHECKING

from Core.Debug.LogData import LogData
from Core.Enums.LogLevel import LogLevel
from Core.EventSystem.Event import Event
from Core.EventSystem.EventType import EventType

if TYPE_CHECKING:
    from Main import MainWindow


class Debug:
    LEVELS = {
        "DEBUG": "\033[90m",
        "INFO": "\033[94m",
        "WARNING": "\033[93m",
        "ERROR": "\033[91m",
        "CRITICAL": "\033[95m",
        "ENDC": "\033[0m",
    }

    SAVE_TO_DISK = True

    LOG_DIRECTORY = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "../../logs"
    )

    MAX_LOG_ENTRIES = 1024

    LOG_BATCH_SIZE = 256
    LOG_FLUSH_INTERVAL_MS = 1000

    MAX_LOG_FILE_SIZE = 16 * 1024 * 1024
    MAX_TOTAL_LOG_SIZE = 1024 * 1024 * 1024

    STACKTRACE_LEVELS = {
        LogLevel.WARNING,
        LogLevel.ERROR,
        LogLevel.CRITICAL
    }

    _main_window: MainWindow | None = None

    log_data: deque[LogData] = deque(maxlen=MAX_LOG_ENTRIES)

    _log_buffer: list[str] = []

    _log_lock = threading.Lock()

    _sequence_counter = itertools.count()

    _flush_thread_started = False
    _shutdown_event = threading.Event()

    @classmethod
    def initialize(cls):
        cls._ensure_log_thread()
        atexit.register(cls.shutdown)

    @classmethod
    def shutdown(cls):
        cls._shutdown_event.set()
        cls._flush_logs()

    @classmethod
    def set_main_window(cls, main_window: MainWindow):
        cls._main_window = main_window

    @staticmethod
    def _get_caller_info(depth: int = 3) -> str:
        try:
            stack = inspect.stack()
            frame_info = stack[depth]

            return (
                f"{frame_info.filename}:"
                f"{frame_info.lineno} "
                f"in {frame_info.function}()"
            )

        except Exception:
            return "Unknown Source"

    @classmethod
    def _ensure_log_thread(cls):
        if cls._flush_thread_started:
            return

        cls._flush_thread_started = True

        thread = threading.Thread(
            target=cls._flush_worker,
            daemon=True
        )

        thread.start()

    @classmethod
    def _flush_worker(cls):
        while not cls._shutdown_event.is_set():
            cls._shutdown_event.wait(
                cls.LOG_FLUSH_INTERVAL_MS / 1000
            )

            cls._flush_logs()

    @classmethod
    def _cleanup_old_logs(cls):
        try:
            files: list[tuple[str, float, int]] = []

            for name in os.listdir(cls.LOG_DIRECTORY):
                if not name.endswith(".log"):
                    continue

                path = os.path.join(
                    cls.LOG_DIRECTORY,
                    name
                )

                if not os.path.isfile(path):
                    continue

                files.append((
                    path,
                    os.path.getmtime(path),
                    os.path.getsize(path)
                ))

            total_size = sum(size for _, _, size in files)

            if total_size <= cls.MAX_TOTAL_LOG_SIZE:
                return

            files.sort(key=lambda x: x[1])

            for path, _, size in files:
                try:
                    os.remove(path)

                    total_size -= size

                    if total_size <= cls.MAX_TOTAL_LOG_SIZE:
                        break

                except Exception as e:
                    print(
                        f"Failed deleting log: {e}",
                        file=sys.stderr
                    )

        except Exception as e:
            print(
                f"Cleanup failed: {e}",
                file=sys.stderr
            )

    @classmethod
    def _flush_logs(cls):
        if not cls.SAVE_TO_DISK:
            return

        with cls._log_lock:
            if not cls._log_buffer:
                return

            pending_logs = ''.join(cls._log_buffer)

            cls._log_buffer.clear()

        try:
            os.makedirs(
                cls.LOG_DIRECTORY,
                exist_ok=True
            )

            encoded_size = len(
                pending_logs.encode("utf-8")
            )

            base_filename = datetime.datetime.now().strftime(
                "%Y-%m-%d"
            )

            index = 0

            while True:
                suffix = f".{index}" if index else ""

                filename = (
                    f"{base_filename}{suffix}.log"
                )

                filepath = os.path.join(
                    cls.LOG_DIRECTORY,
                    filename
                )

                if not os.path.exists(filepath):
                    break

                current_size = os.path.getsize(filepath)

                if (
                    current_size + encoded_size
                    <= cls.MAX_LOG_FILE_SIZE
                ):
                    break

                index += 1

            with open(
                filepath,
                "a",
                encoding="utf-8"
            ) as f:
                f.write(pending_logs)

            cls._cleanup_old_logs()

        except Exception as e:
            print(
                f"Failed writing logs: {e}",
                file=sys.stderr
            )

    @classmethod
    def _create_stacktrace(cls) -> list[inspect.FrameInfo]:
        return inspect.stack()[2:]

    @classmethod
    def _log(
        cls,
        level: LogLevel,
        message: str
    ):
        cls._ensure_log_thread()

        timestamp = (
            datetime.datetime.now()
            .strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        )

        source = cls._get_caller_info()

        stacktrace: list[inspect.FrameInfo] | None = None

        if level in cls.STACKTRACE_LEVELS:
            stacktrace = cls._create_stacktrace()

        data = LogData(
            sequence=next(cls._sequence_counter),
            timestamp=timestamp,
            level=level,
            message=message,
            source=source,
            traceback=stacktrace
        )

        with cls._log_lock:
            cls.log_data.append(data)

            if cls.SAVE_TO_DISK:
                cls._log_buffer.append(
                    f"[{timestamp}] "
                    f"[{level.value}] "
                    f"{message} "
                    f"({source})\n"
                )

                should_flush = (
                    len(cls._log_buffer)
                    >= cls.LOG_BATCH_SIZE
                )

            else:
                should_flush = False

        color = cls.LEVELS.get(level.name, "")
        endc = cls.LEVELS["ENDC"]

        output = (
            sys.stderr
            if level in (
                LogLevel.ERROR,
                LogLevel.CRITICAL
            )
            else sys.stdout
        )

        print(
            f"{color}[{timestamp}] "
            f"[{level.value}] "
            f"{message} "
            f"({source}){endc}",
            file=output
        )

        if cls._main_window:
            try:
                cls._main_window.event_bus.publish(
                    Event(
                        type=EventType.EVENT_LOG_ADDED.value,
                        source=source,
                        payload={
                            "data": data
                        }
                    )
                )

            except Exception as e:
                print(
                    f"Event publish failed: {e}",
                    file=sys.stderr
                )

        if stacktrace:
            print(
                ''.join(traceback.format_list(
                    [
                        traceback.FrameSummary(
                            frame.filename,
                            frame.lineno,
                            frame.function,
                            line=frame.code_context[frame.index].strip()
                            if frame.code_context and frame.index is not None
                            else None
                        )
                        for frame in stacktrace
                    ]
                )),
                file=sys.stderr
            )

        if should_flush:
            cls._flush_logs()

    @classmethod
    def log(cls, message: str):
        cls._log(LogLevel.INFO, message)

    @classmethod
    def log_debug(cls, message: str):
        cls._log(LogLevel.DEBUG, message)

    @classmethod
    def log_warning(cls, message: str):
        cls._log(LogLevel.WARNING, message)

    @classmethod
    def log_error(cls, message: str):
        cls._log(LogLevel.ERROR, message)

    @classmethod
    def log_critical(cls, message: str):
        cls._log(LogLevel.CRITICAL, message)