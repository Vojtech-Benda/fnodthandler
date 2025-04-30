from pydantic import BaseModel
from typing import Dict, Union


class Job(BaseModel):
    request_id: str = ""
    pacs: dict = {"ip": "", "port": "", "aetitle": ""}
    process_name: str = ""
    notify_email: str = ""
    series_uid_list: list = []
    date: str = ""
    start_time: str = ""
    finish_time: str = ""
    status: bool = "pending"