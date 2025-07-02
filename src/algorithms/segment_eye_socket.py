import sys
import os
from src.logger import setup_logger
from src.process_result import ProcessResult, StatusCodes


def seg_ct_eye_socket(data_dirs: list[str], output_dir: str = "."):
    raise NotImplemented


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: dcm2other.py <input_dir> <output_datatype> [optional] <output_dir>")
        print("Supported output datatypes: mha, nifti")
        
        output_dir = sys.argv[3] if sys.argv[3] else "." 
    seg_ct_eye_socket(sys.argv[1], output_dir, sys.argv[2])