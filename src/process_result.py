from enum import Enum
from typing import Optional
from dataclasses import dataclass


class StatusCodes(Enum):
    NONE = -1
    SUCCESS = 0
    WARNING = 1
    DOWNLOAD_ERROR = 2
    CONVERSION_ERROR = 3
    FILE_ERROR = 97
    COMMANDLINE_ERROR = 98
    UNKNOWN_ERROR = 99


@dataclass
class ProcessResult:
    code: StatusCodes = StatusCodes.NONE
    message: str = None
    stdout: Optional[str] = None
    process: Optional[str] = None
        
    def mark_success(self, message: str, **kwargs):
        self.code = StatusCodes.SUCCESS
        self.message = message
        for key, value in kwargs.items():
            setattr(self, key, value)
        
    def mark_failure(self, code: StatusCodes, message: str, **kwargs):
        if code == StatusCodes.SUCCESS:
            raise ValueError("failure must be error code")
        self.code = code
        self.message = message
        for key, value in kwargs.items():
            setattr(self, key, value)
        
    def mark_warning(self, message: str, **kwargs):
        self.code = StatusCodes.WARNING
        self.message = message
        for key, value in kwargs.items():
            setattr(self, key, value)
        
    def is_good(self) -> bool:
        return self.code in [StatusCodes.SUCCESS, StatusCodes.WARNING]
    
    def is_bad(self) -> bool:
        return self.code in [StatusCodes.UNKNOWN_ERROR, StatusCodes.DOWNLOAD_ERROR, StatusCodes.CONVERSION_ERROR]
    
    def format_result(self) -> str:
        msg = f"process: {self.process}\nstatus_code: {self.code}\nmessage: {self.message}"
        if self.stdout:
            msg += f"\nstdout: {self.stdout}"
        return msg
        