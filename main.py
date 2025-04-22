from fastapi import FastAPI, Request, Form, BackgroundTasks
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi_utils.tasks import repeat_every
from contextlib import asynccontextmanager

import os
import random
import string
from datetime import datetime

from src.download_dcm import download_dcm
from src.job import Job
from src.utils import split_pacs_fields


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[INFO] starting app...")
    await check_queue() # needs to run once to register with lifespan and FastAPI
    app.add_event_handler("startup", check_queue)
    
    if os.path.exists("./input"):
        os.makedirs("./input", exist_ok=True)
        print("[INFO] created directory './input'")
    if os.path.exists("./output"):
        os.makedirs("./output", exist_ok=True)
        print("[INFO] created directory './output'")
    if os.path.exists("./processed"):
        os.makedirs("./processed", exist_ok=True)
        print("[INFO] created directory './procesed'")
    
    yield
    print("[INFO] shutting down app...")

app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory="templates/")

job_queue: list[Job] = []


@app.get("/", response_class=HTMLResponse)
def display_form(request: Request):
    return templates.TemplateResponse("form.html", context={"request": request})


@app.post("/", response_class=HTMLResponse)
def handle_form(request: Request, 
                pacs_select: str = Form(...), 
                series_uids: str = Form(...),
                process_select: str = Form(...), 
                notify_email: str = Form(...)):
    request_id = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    request_id += "-" + datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    pacs_ae, pacs_ip, pacs_port = split_pacs_fields(pacs_select)

    cleaned_uids = series_uids.replace("\r\n", "").replace("\n", "").strip().split(",")
    new_job = Job(request_id=request_id,
                  pacs={"ip": pacs_ip, "port": pacs_port, "aetitle": pacs_ae},
                  process_name=process_select,
                  notify_email=notify_email,
                  series_uid_list=cleaned_uids)
    job_queue.append(new_job)
    print(f"[INFO] added new job {new_job}")
    return templates.TemplateResponse("form.html", context={"request": request, 
                                                            "pacs_select": pacs_select,
                                                            "process_select": process_select,
                                                            "series_uids": series_uids,
                                                            "notify_email": notify_email})
    
@repeat_every(seconds=5)
async def check_queue():
    if len(job_queue) != 0:
        print("[INFO] checking queue...")
        job = job_queue[0]
        number_of_series = download_dcm(job.request_id, job.pacs, job.series_uid_list)
        
        if number_of_series != 0:
            print("[INFO] starting process...")
        removed_job = job_queue.pop(0)
        print(f"[INFO] removed job {removed_job}")
    else:
        print("[INFO] no job to process")