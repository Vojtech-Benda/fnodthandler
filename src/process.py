from functools import partial
from src.algorithms.dicom_convert import dcm2other
from src.algorithms.comp2comp import comp2comp
from src.algorithms.segment_eye_socket import seg_ct_eye_socket

PROCESS_DISPATCH = {
    "dcm2mha": partial(dcm2other, output_datatype="mha"),
    "dcm2nifti": partial(dcm2other, output_datatype="nifti"),
    "seg_ct_c2c_sma": partial(comp2comp, pipeline="spine_muscle_adipose"),
    "seg_ct_eye_socket": seg_ct_eye_socket
}
    
