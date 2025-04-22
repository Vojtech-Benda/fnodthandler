import sys
import os
import subprocess

def download_dcm(request_id: str, pacs: dict, series_uids: list):
    result = None
    failed_series = []
    for serie_uid in series_uids:
        output_dir = f"./input/{request_id}/{serie_uid}"
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
            print(f"[ERROR] script movescu.py failed with exit code {er.returncode}")
            print(f"[ERROR] script arguments {pacs}, download dir {output_dir}, series uid {serie_uid}")
            failed_series.append(serie_uid)
            os.rmdir(output_dir)
            
        # failed C-MOVE request can pass above try-except block
        if len(os.listdir(output_dir)) == 0:
            failed_series.append(serie_uid)
            os.rmdir(output_dir)
            
    found_series = len(os.listdir(f"./input/{request_id}"))
    print(f"[INFO] downloaded {found_series} out of {len(series_uids)} series")
    
    if len(failed_series) != 0:
        print(f"[INFO] missing series {failed_series}")
        
    return found_series        