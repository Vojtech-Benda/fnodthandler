from pydantic import BaseModel
from typing import Optional, Dict


class Job(BaseModel):
    request_id: str = ""
    pacs: dict[str, str] = {"ip": "", "port": "", "aetitle": ""}
    process_name: str = ""
    notify_email: str = ""
    uid_list: list[str] = []
    date: str = ""
    start_time: str = ""
    finish_time: str = ""
    status: str = "pending"
    status_detail: str = ""
    additional_options: Optional[Dict[str, str]] = {}
    
    
class ProcessedData(BaseModel):
    request_id: str = ""
    process_name: str = ""
    date: str = ""
    finish_time: str = ""
    file_size: str = ""