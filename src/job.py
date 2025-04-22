from pydantic import BaseModel
from typing import Dict, Union


class Job(BaseModel):
    request_id: str = ""
    pacs: dict = {"ip": "", "port": "", "aetitle": ""}
    process_name: str = ""
    notify_email: str = ""
    series_uid_list: list = []
    finished: bool = False