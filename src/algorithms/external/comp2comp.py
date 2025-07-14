import sys
import os
import subprocess
import logging

from src.task_result import TaskResult, StatusCodes
from pathlib import Path

from src.utils import read_env

logger = logging.getLogger("uvicorn")

task_paths = read_env(parent="algorithms", child="comp2comp")


EXECUTABLE_PATH = Path(task_paths['exec_path']).expanduser()
SCRIPT_PATH = Path(task_paths['script_path']).expanduser()


def comp2comp(data_dirs: list[str], output_dir: str = ".", **kwargs):
    save_segmentations = kwargs.get("save_segmentations", False)
    pipeline = kwargs.get('pipeline_select')
    
    logger.info(f"starting comp2comp, pipeline {pipeline}")
    logger.debug(f"subprocess args: {EXECUTABLE_PATH} {SCRIPT_PATH} {pipeline}")
    logger.debug(f"input paths: {"\n".join(data_dirs)}")
    
    logger.info(f"segmenting {len(data_dirs)} data")
    result = TaskResult()
    sub_result: subprocess.CompletedProcess = None
    sub_results = []
    
    for directory in data_dirs:
        command = [EXECUTABLE_PATH, SCRIPT_PATH, pipeline, "-i", directory, "-o", output_dir]
        if save_segmentations:
            command.append("--save_segmentations")
            
        try:
            sub_result = subprocess.run(command, 
                                        capture_output=True,
                                        text=True,
                                        check=True)
            sub_results.append(sub_result.returncode)
        except subprocess.CalledProcessError as err:
            logger.error(f"comp2comp failed with exit code {err.returncode}")
            logger.error(err.stderr)
            os.rmdir(output_dir)
    
    if sum(sub_results) == 0:
        result.mark_success("segmentation finished successfuly")
    else:
        result.mark_failure("segmentation failed")
    
    return result