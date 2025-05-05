import sys
import os
import subprocess

from .logger import setup_logger


fno_logger = setup_logger("fnodthandler")

def download_dcm(request_id: str, pacs: dict, series_uids: list):
    result = None
    failed_series = []
    for serie_uid in series_uids:
        output_dir = f"./input/{serie_uid}"
        fno_logger.debug(f"creating download directory \"{output_dir}\"")
        os.makedirs(output_dir, exist_ok=True)
        try: 
            result = subprocess.run([sys.executable,
                                     "./src/algorithms/movescu.py",
                                     pacs['ip'], pacs['port'],
                                     "-aec", pacs['aetitle'],
                                     "-aet", "VOJTPC",
                                     "-aem", "VOJTPC",
                                     "--store", "--store-port", "2000",
                                     "-od", output_dir,
                                     "-k", f"SeriesInstanceUID={serie_uid}",
                                     "-q"
                                     ])
        except subprocess.CalledProcessError as er:
            fno_logger.error(f"script movescu.py failed with exit code {er.returncode}")
            fno_logger.error(f"script arguments {pacs}, download dir {output_dir}, series uid {serie_uid}")
            failed_series.append(serie_uid)
            os.rmdir(output_dir)
            
        # failed C-MOVE request can pass above try-except block
        if len(os.listdir(output_dir)) == 0:
            failed_series.append(serie_uid)
            os.rmdir(output_dir)
            
    downloaded_uids = [uid for uid in serie_uid if uid in os.listdir("./input")]
    fno_logger.info(f"downloaded {len(downloaded_uids)} out of {len(series_uids)} series")
    
    if len(failed_series) != 0:
        fno_logger.warning(f"failed downloading uids:\n{",\n".join(failed_series)}")
    
    if len(failed_series) == len(series_uids):
        return -1
    return result.returncode