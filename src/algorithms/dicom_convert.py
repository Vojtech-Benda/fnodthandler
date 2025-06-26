import sys
import SimpleITK as sitk
import os
from ..logger import setup_logger

fno_logger = setup_logger("fnodthandler")

SITK_IMAGE_TYPES = {
    "mha": "mha",
    "nifti": "nii.gz",
    "nrrd": "nrrd"
}


def dcm2other(data_dirs: str, output_dir: str = ".", output_datatype: str = "mha"):
    cond = 0
    fno_logger.info(f"converting {len(data_dirs)} data")
    reader = sitk.ImageSeriesReader()
    
    for directory in data_dirs:
        dicom_names = reader.GetGDCMSeriesFileNames(directory)
        reader.SetFileNames(dicom_names)
        image: sitk.Image = None
        try:
            image = reader.Execute()
        except:
            # return -1
            fno_logger.error(f"unable to read image data: \"{directory}\"")
            continue
        
        filename = os.path.join(output_dir, os.path.basename(directory) + "." + SITK_IMAGE_TYPES[output_datatype])
        fno_logger.info(f"writing as {output_datatype.upper()} to \"{filename}\"")
        if os.path.exists(filename):
            fno_logger.info(f"file exists, overwriting: \"{filename}\"")
        try:
            sitk.WriteImage(image, filename)
            fno_logger.info(f"writing {output_datatype.upper()} finished")
            cond = 0
        except RuntimeError as err:
            fno_logger.error(f"writing {output_datatype.upper()} failed")
            fno_logger.error(err)
            cond = -1
            
    return cond
        # else:
        #     print("[dcm2mha] SeriesInstanceUID not found")
        #     print("[dcm2mha] Unable to save as MHA")
        #     return -1
    
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: dcm2other.py <input_dir> <output_datatype> [optional] <output_dir>")
        print("Supported output datatypes: mha")
        
    dcm2other(sys.argv[1], sys.argv[2])