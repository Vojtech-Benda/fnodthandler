import multiprocessing.process
import multiprocessing.spawn
import sys
import os
import subprocess
from pathlib import Path

from src.logger import setup_logger
from src.process_result import ProcessResult, StatusCodes
from dotenv import load_dotenv
import multiprocessing


fno_logger = setup_logger("fnodthandler")
load_dotenv()



pipeline_dict = {
    "seg_ct_c2c_sma": "spine_muscle_adipose_tissue"
}


EXECUTABLE_PATH = os.getenv("C2C_EXEC_PATH")
SCRIPT_PATH = os.getenv("C2C_SCRIPT_PATH")


def comp2comp(data_dirs: list[str], output_dir: str = ".", pipeline: str = "seg_c2c_sma"):
    fno_logger.info(f"running comp2comp {pipeline_dict[pipeline]}")
    fno_logger.debug(f"subprocess args: {EXECUTABLE_PATH} {SCRIPT_PATH} {pipeline_dict[pipeline]}")
    fno_logger.debug(f"input paths: {"\n".join(data_dirs)}")
    
    fno_logger.info(f"segmenting {len(data_dirs)} data")
    result = ProcessResult()
    sub_result: subprocess.CompletedProcess = None
    sub_results = []
    
    for directory in data_dirs:
        try:
            sub_result = subprocess.run([
                EXECUTABLE_PATH,
                SCRIPT_PATH,
                pipeline_dict[pipeline],
                "-i", directory,
                "-o", output_dir,
                "--save_segmentations"
            ], 
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