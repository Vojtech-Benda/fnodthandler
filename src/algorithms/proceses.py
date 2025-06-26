from functools import partial
from .dicom_convert import dcm2other
from .. import errors


PROCESS_DISPATCH = {
    "dcm2mha": partial(dcm2other, output_datatype="mha"),
    "dcm2nifti": partial(dcm2other, output_datatype="nifti")
}