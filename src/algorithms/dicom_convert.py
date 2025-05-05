import sys
import SimpleITK as sitk
import os
from ..logger import setup_logger

fno_logger = setup_logger("fnodthandler")

def dcm_convert(data_dirs: str, output_datatype: str, output_dir: str = "."):
    cond = 0
    PROCESS_NAME = f"dcm2{output_datatype}"
    # data_dirs = os.listdir(input_dir)
    fno_logger.info(f"converting {len(data_dirs)} data")
    reader = sitk.ImageSeriesReader()
    
    # reader.LoadPrivateTagsOn()
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
        # print(f"[{PROCESS_NAME}] Image: size {image.GetSize()}, pixel type {image.GetPixelIDTypeAsString()}, spacing {image.GetSpacing()}")
        filename = os.path.join(output_dir, os.path.basename(directory) + f".{output_datatype}")
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
        print("Usage: dcm_convert.py <input_dir> <output_datatype> [optional] <output_dir>")
        print("Supported output datatypes: mha")
        
    dcm_convert(sys.argv[1], sys.argv[2])