import sys
import os
import subprocess

from src.logger import setup_logger
from src.process_result import ProcessResult, StatusCodes
from dotenv import load_dotenv
from pathlib import Path

from src.utils import read_env

fno_logger = setup_logger("fnodthandler")
# load_dotenv()

process_paths = read_env(parent="algorithms", child="comp2comp")

# pipeline_dict = {
#     "seg_ct_c2c_sma": "spine_muscle_adipose_tissue"
# }

EXECUTABLE_PATH = Path(process_paths['exec_path']).expanduser()
SCRIPT_PATH = Path(process_paths['script_path']).expanduser()


def comp2comp(data_dirs: list[str], output_dir: str = ".", **kwargs):
    save_segmentations = kwargs.get("save_segmentations", False)
    pipeline = kwargs.get('pipeline_select')
    
    fno_logger.info(f"starting comp2comp, pipeline {pipeline}")
    fno_logger.debug(f"subprocess args: {EXECUTABLE_PATH} {SCRIPT_PATH} {pipeline}")
    fno_logger.debug(f"input paths: {"\n".join(data_dirs)}")
    
    fno_logger.info(f"segmenting {len(data_dirs)} data")
    result = ProcessResult()
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
            fno_logger.error(f"comp2comp failed with exit code {err.returncode}")
            fno_logger.error(err.stderr)
            os.rmdir(output_dir)
    
    if sum(sub_results) == 0:
        result.mark_success("segmentation finished successfuly")
    else:
        result.mark_failure("segmentation failed")
    
    return result