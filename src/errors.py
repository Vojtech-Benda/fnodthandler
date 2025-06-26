from enum import Enum


class StatusCodes(Enum):
    NONE = 0
    DOWNLOAD_OK = 10
    DOWNLOAD_FAIL = 11
    DOWNLOAD_PARTIAL = 12
    PROCESS_OK = 20
    PROCESS_FAIL = 21
    PROCESS_PARTIAL = 22
    


class Condition:
    def __init__(self, status_code: StatusCodes = StatusCodes.NONE):
        # self.state: bool = state
        self.status_code: StatusCodes = status_code
        self.reason: str = None
        