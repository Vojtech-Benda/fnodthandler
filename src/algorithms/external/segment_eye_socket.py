import sys
import os
import logging

from src.task_result import TaskResult, StatusCodes


logger = logging.getLogger("uvicorn")


def segment_eye_socket(data_dirs: list[str], output_dir: str = "."):
    print(data_dirs, output_dir)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: dcm2other.py <input_dir> [optional] <output_dir>")
         
    segment_eye_socket(sys.argv[1], sys.argv[2])