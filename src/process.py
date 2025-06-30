from functools import partial
from src.algorithms.dicom_convert import dcm2other


PROCESS_DISPATCH = {
    "dcm2mha": partial(dcm2other, output_datatype="mha"),
    "dcm2nifti": partial(dcm2other, output_datatype="nifti")
}


# class StatusCodes(Enum):
#     SUCCESS = 0
#     WARNING = 1
#     DOWNLOAD_ERROR = 2
#     CONVERSION_ERROR = 3
#     UNKNOWN_ERROR = 99


# @dataclass
# class ProcessResult:
#     code: int = 0
#     # success: bool = False
#     message: str = None
#     stdout: Optional[str] = None
#     process = Optional[str] = None
            
#     # def set_condition(self, code: int, message: str = None, stdout: Optional[str] = None):
#     #     self.code = code
#     #     self.message = message
#     #     self.stdout = stdout
        
#     @classmethod
#     def success(cls, message: str, **kwargs):
#         return cls(code=StatusCodes.SUCCESS, message=message, **kwargs)
        
#     @classmethod
#     def failure(cls, code: int, message: str, **kwargs):
#         if code == StatusCodes.SUCCESS or code == 0:
#             raise ValueError("failure must be non-zero code")
#         return cls(code=code, message=message, **kwargs)
        
#     @classmethod
#     def warning(cls, message: str, **kwargs):
#         return cls(code=StatusCodes.WARNING, message=message, **kwargs)
    
#     def format_result(self) -> str:
#         msg = f"process: {self.process}\nstatus_code: {self.code}\nmessage: {self.message}"
#         if self.stdout:
#             msg += f"\nstdout: {self.stdout}"
#         return msg
        
    
