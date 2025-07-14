import sys
import os
import logging
from pathlib import Path
from argparse import ArgumentParser

import SimpleITK as sitk
# from src.logger import setup_logger
from src.task_result import TaskResult, StatusCodes
# fno_logger = setup_logger("fnodthandler")

logging.basicConfig(
    format="%(asctime)s %(levelname)s:\t%(message)s",
    level=logging.INFO,
    datefmt="%H:%M:%S")


SITK_IMAGE_TYPES = {
    "mha": "mha",
    "nii_gz": "nii.gz",
    "nii": "nii",
    "nrrd": "nrrd"
}


def get_args():
    parser = ArgumentParser(prog="dcm2other", description="convert DICOM image data type")
    
    parser.add_argument("-i", "--input_dir", nargs='+', type=str, help="input directories containing DICOM files", required=True)
    parser.add_argument("-o", "--output_dir", type=str, help="output directory to store converted files", default="./converted")
    parser.add_argument("-d", "--datatype", type=str, help="output datatype", choices=SITK_IMAGE_TYPES.keys(), required=True)
    return parser.parse_args()

def dcm2other(input_dirs: list[str], output_dir: str = "./converted", **kwargs):
    # fno_logger.info(f"converting {len(data_dirs)} data")
    logging.info(f"found {len(input_dirs)} directories with DICOM files")
    
    reader = sitk.ImageSeriesReader()
    
    output_dir: Path = Path(output_dir).absolute()
    if not output_dir.exists():
        os.makedirs(output_dir, exist_ok=True)
        
    result = TaskResult()
    processed_dirs = [False] * len(input_dirs)
    for idx, directory in enumerate(input_dirs):
        dicom_names = reader.GetGDCMSeriesFileNames(directory)
        reader.SetFileNames(dicom_names)
        image: sitk.Image = None
        try:
            image = reader.Execute()
        except:
            # fno_logger.error(f"unable to read image data: \"{directory}\"")
            logging.error(f"unable to read image data: '{directory}'")
            continue
        
        output_datatype = kwargs.get("output_datatype")
        filename = os.path.join(output_dir, os.path.basename(directory) + "." + SITK_IMAGE_TYPES[output_datatype])
        logging.info(f"writing '{filename}' as {output_datatype.upper()}")
        if os.path.exists(filename):
            logging.info(f"file exists, overwriting: '{filename}'")
        try:
            sitk.WriteImage(image, filename)
            logging.info(f"conversion finished '{filename}'")
            processed_dirs[idx] = True
        except RuntimeError as err:
            logging.error("conversion failed")
            logging.error(err)
    
    if sum(processed_dirs) == len(processed_dirs):
        result.mark_success("all input dirs processed")
    elif sum(processed_dirs) == 0:
        result.mark_failure(StatusCodes.CONVERSION_ERROR, "none input dirs processed")
    else:
        result.mark_warning("some input dirs processed")
    return result
    
if __name__ == "__main__":
    args = get_args()
    
    dcm2other(args.input_dir, args.output_dir, output_datatype=args.datatype)