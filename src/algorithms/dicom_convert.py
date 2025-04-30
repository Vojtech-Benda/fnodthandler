import sys
import SimpleITK as sitk
import os

def dcm_convert(input_dir: str, output_datatype: str, output_dir: str = "."):
    PROCESS_NAME = f"dcm2{output_datatype}"
    data_dirs = os.listdir(input_dir)
    print(f"[{PROCESS_NAME}][INFO] found {len(data_dirs)} in {input_dir}")
    reader = sitk.ImageSeriesReader()
    
    # reader.LoadPrivateTagsOn()
    for dir in data_dirs:
        dicom_names = reader.GetGDCMSeriesFileNames(os.path.join(input_dir, dir))
        reader.SetFileNames(dicom_names)
        image: sitk.Image = None
        try:
            image = reader.Execute()
        except:
            # return -1
            print(f"[{PROCESS_NAME}][ERROR] unable to read image: \"{dir}\"")
            continue
        # print(f"[{PROCESS_NAME}] Image: size {image.GetSize()}, pixel type {image.GetPixelIDTypeAsString()}, spacing {image.GetSpacing()}")
        print(f"[{PROCESS_NAME}][INFO] writing as {output_datatype.upper()} to \"{output_dir}/{dir}\"")
        filename = os.path.join(output_dir, dir + f".{output_datatype}")
        if os.path.exists(filename):
            print(f"[{PROCESS_NAME}][WARN] file exists, overwriting: \"{filename}\"")
        try:
            sitk.WriteImage(image, filename)
            print(f"[{PROCESS_NAME}][INFO] DICOM saved as {output_datatype.upper()}")
        except:
            print(f"[{PROCESS_NAME}][ERROR] failed to write as {output_datatype.upper()}: \"{filename}\"")
    return 0
        # else:
        #     print("[dcm2mha] SeriesInstanceUID not found")
        #     print("[dcm2mha] Unable to save as MHA")
        #     return -1
    
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: dcm_convert.py <input_dir> <output_datatype> [optional] <output_dir>")
        print("Supported output datatypes: mha")
        
    dcm_convert(sys.argv[1], sys.argv[2])