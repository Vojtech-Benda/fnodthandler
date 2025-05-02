from pydantic import BaseModel


class Job(BaseModel):
    request_id: str = ""
    pacs: dict[str, str] = {"ip": "", "port": "", "aetitle": ""}
    process_name: str = ""
    notify_email: str = ""
    series_uid_list: list[str] = []
    date: str = ""
    start_time: str = ""
    finish_time: str = ""
    status: bool = "pending"