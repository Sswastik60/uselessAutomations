"""Clean, thread-safe activity logger with PySide6 signals."""

import sys
from datetime import datetime
from enum import Enum
from typing import List, Optional
from pathlib import Path
from PySide6.QtCore import QObject, Signal


class LogLevel(str, Enum):
    INFO = "INFO"
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "ERROR"


class LogEntry:
    def __init__(self, message: str, level: LogLevel = LogLevel.INFO, timestamp: Optional[datetime] = None):
        self.message = message
        self.level = level
        self.timestamp = timestamp or datetime.now()

    @property
    def formatted_time(self) -> str:
        return self.timestamp.strftime("%H:%M:%S")

    def __str__(self) -> str:
        return f"{self.formatted_time} [{self.level.value}] {self.message}"


class ActivityLogger(QObject):
    """Activity logger that broadcasts log entries to the UI in a thread-safe manner."""
    entry_added = Signal(object)  # Emits LogEntry

    _instance: Optional["ActivityLogger"] = None

    def __init__(self, log_to_file: bool = True, log_file_path: Optional[str] = None):
        super().__init__()
        self._entries: List[LogEntry] = []
        self._log_to_file = log_to_file
        self._file_path = log_file_path or str(Path("hackfill.log").absolute())

    @classmethod
    def get_instance(cls) -> "ActivityLogger":
        if cls._instance is None:
            cls._instance = ActivityLogger()
        return cls._instance

    def log(self, message: str, level: LogLevel = LogLevel.INFO) -> LogEntry:
        """Create, store, and emit a new log entry."""
        entry = LogEntry(message=message, level=level)
        self._entries.append(entry)

        # Write to file if enabled
        if self._log_to_file:
            try:
                with open(self._file_path, "a", encoding="utf-8") as f:
                    f.write(f"{str(entry)}\n")
            except Exception:
                pass

        # Broadcast via Qt signal
        self.entry_added.emit(entry)
        return entry

    def info(self, message: str) -> LogEntry:
        return self.log(message, LogLevel.INFO)

    def success(self, message: str) -> LogEntry:
        return self.log(message, LogLevel.SUCCESS)

    def warning(self, message: str) -> LogEntry:
        return self.log(message, LogLevel.WARNING)

    def error(self, message: str) -> LogEntry:
        return self.log(message, LogLevel.ERROR)

    def get_entries(self) -> List[LogEntry]:
        return list(self._entries)

    def clear(self) -> None:
        self._entries.clear()


def get_logger() -> ActivityLogger:
    """Helper to access singleton activity logger."""
    return ActivityLogger.get_instance()
