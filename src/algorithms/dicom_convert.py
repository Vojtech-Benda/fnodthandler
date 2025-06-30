import sys
import SimpleITK as sitk
import os
# from ..logger import setup_logger
from src.logger import setup_logger
# from ..process_result import ProcessResult, StatusCodes
from src.process_result import ProcessResult, StatusCodes


fno_logger = setup_logger("fnodthandler")

SITK_IMAGE_TYPES = {
    "mha": "mha",
    "nifti": "nii.gz",
    "nrrd": "nrrd"
}


def dcm2other(data_dirs: str, output_dir: str = ".", output_datatype: str = "mha"):
    # cond = 0
    fno_logger.info(f"converting {len(data_dirs)} data")
    reader = sitk.ImageSeriesReader()
    
    result = ProcessResult()
    processed_dirs = [False] * len(data_dirs)
    for idx, directory in enumerate(data_dirs):
        dicom_names = reader.GetGDCMSeriesFileNames(directory)
        reader.SetFileNames(dicom_names)
        image: sitk.Image = None
        try:
            image = reader.Execute()
        except:
            fno_logger.error(f"unable to read image data: \"{directory}\"")
            continue
        
        filename = os.path.join(output_dir, os.path.basename(directory) + "." + SITK_IMAGE_TYPES[output_datatype])
        fno_logger.info(f"writing as {output_datatype.upper()} to \"{filename}\"")
        if os.path.exists(filename):
            fno_logger.info(f"file exists, overwriting: \"{filename}\"")
        try:
            sitk.WriteImage(image, filename)
            fno_logger.info(f"writing {output_datatype.upper()} finished")
            processed_dirs[idx] = True
            # cond = 0
        except RuntimeError as err:
            fno_logger.error(f"writing {output_datatype.upper()} failed")
            fno_logger.error(err)
            # cond = -1
    
    if sum(processed_dirs) == len(processed_dirs):
        result.mark_success("all input dirs processed")
    elif sum(processed_dirs) == 0:
        result.mark_failure(StatusCodes.CONVERSION_ERROR, "none input dirs processed")
    else:
        result.mark_warning("some input dirs processed")
    return result
    
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: dcm2other.py <input_dir> <output_datatype> [optional] <output_dir>")
        print("Supported output datatypes: mha")
        
    dcm2other(sys.argv[1], sys.argv[2])