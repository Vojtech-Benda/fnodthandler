import sys
import os
import subprocess

from src.logger import setup_logger
from src.process_result import ProcessResult, StatusCodes


fno_logger = setup_logger("fnodthandler")


pipeline_dict = {
    "seg_c2c_sma": "spine_muscle_adipose_tissue"
}


EXECUTABLE_PATH = "/home/vojt/miniforge3/envs/c2c-env39/bin/python"
SCRIPT_PATH = "./src/algorithms/Comp2Comp/bin/C2C"


def comp2comp(data_dirs: list[str], output_dir: str = ".", pipeline: str = "seg_c2c_sma"):
    fno_logger.info(f"segmenting {len(data_dirs)} data")
    fno_logger.info(f"starting comp2comp {pipeline_dict[pipeline]}")
    
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