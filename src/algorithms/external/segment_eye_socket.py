import sys
import os
from src.logger import setup_logger
from src.task_result import TaskResult, StatusCodes


def segment_eye_socket(data_dirs: list[str], output_dir: str = "."):
    print(data_dirs, output_dir)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: dcm2other.py <input_dir> <output_datatype> [optional] <output_dir>")
        print("Supported output datatypes: mha, nifti")
        
        output_dir = sys.argv[3] if sys.argv[3] else "." 
    segment_eye_socket(sys.argv[1], output_dir, sys.argv[2])