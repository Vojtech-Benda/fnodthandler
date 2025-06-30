from pydantic import BaseModel


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
    
    
class ZipData(BaseModel):
    request_id: str = ""
    process_name: str = ""
    date: str = ""
    finish_time: str = ""
    file_size: str = ""