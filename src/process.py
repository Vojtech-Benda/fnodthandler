from functools import partial
from src.algorithms.dicom_convert import dcm2other


PROCESS_DISPATCH = {
    "dcm2mha": partial(dcm2other, output_datatype="mha"),
    "dcm2nifti": partial(dcm2other, output_datatype="nifti")
}
    
