import sys
import os
import subprocess

from src.logger import setup_logger
from src.process_result import ProcessResult, StatusCodes
from src.utils import read_env

fno_logger = setup_logger("fnodthandler")

env_vars = read_env()

receiver_aetitle = env_vars['aet']
receiver_store_port = env_vars['store_port']
fno_logger.info(f"movescu destination is {receiver_aetitle}:{receiver_store_port}")

def download_dcm(pacs: dict, series_uids: list):
    sub_result: subprocess.CompletedProcess = None
    failed_uids = []
    for serie_uid in series_uids:
        output_dir = f"./input/{serie_uid}"
        fno_logger.debug(f"creating download directory \"{output_dir}\"")
        os.makedirs(output_dir, exist_ok=True)
        try: 
            command = [sys.executable, "./src/algorithms/movescu.py", pacs['ip'], pacs['port'], "-aec", pacs['aetitle'],
                       "-aet", receiver_aetitle, "-aem", receiver_aetitle, "--store", "--store-port", str(receiver_store_port),
                       "-od", output_dir, "-k", "QueryRetrieveLevel=SERIES", "-k", f"SeriesInstanceUID={serie_uid}"]
            sub_result = subprocess.run(command, capture_output=True)
        except subprocess.CalledProcessError as er:
            fno_logger.error(f"script movescu.py failed with exit code {er.returncode}")
            fno_logger.error(f"script arguments {pacs}, download dir {output_dir}, series uid {serie_uid}")
            failed_uids.append(serie_uid)
            os.rmdir(output_dir)
            
        # failed C-MOVE request can pass above try-except block
        if len(os.listdir(output_dir)) == 0:
            failed_uids.append(serie_uid)
            os.rmdir(output_dir)
            
    downloaded_uids = [uid for uid in series_uids if uid in os.listdir("./input")]
    fno_logger.info(f"downloaded {len(downloaded_uids)} out of {len(series_uids)} series")
    
    result = ProcessResult()
    
    if len(failed_uids) != 0:
        result.mark_warning("C-MOVE: some files failed to download", stdout=sub_result.stdout)
        fno_logger.warning(result.format_result())
        fno_logger.warning(f"failed uids:\n{"\n".join(failed_uids)}")
        return result
    
    elif len(failed_uids) == len(series_uids):
        result.mark_failure(StatusCodes.DOWNLOAD_ERROR, "C-MOVE: all files failed to downloaded", stdout=sub_result.stdout)
        fno_logger.error(result.format_result())
        fno_logger.error(f"failed uids:\n{"\n".join(failed_uids)}")
    else:
        result.mark_success("download finished successfuly")
    return result