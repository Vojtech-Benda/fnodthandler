from fastapi import FastAPI, Request, Form
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi_utils.tasks import repeat_every
from contextlib import asynccontextmanager

import os
import random
import string
import json
import aiosqlite
import asyncio
import shutil
from datetime import datetime

from src.algorithms import dicom_convert
from src.download_dcm import download_dcm
from src.job import Job
from src import utils
from src import history
from src.logger import setup_logger


PROCESS_NAME = "main"
fno_logger = setup_logger("fnodthandler")

def main():
    app = FastAPI(lifespan=lifespan)
    app.mount("/static", StaticFiles(directory="static"), name="static")
    return app

@asynccontextmanager
async def lifespan(app: FastAPI):
    await check_queue() # needs to run once to register with lifespan and FastAPI
    app.add_event_handler("startup", check_queue)
    
    if not os.path.exists("jobs_history.db"):
        await history.init_db()
    
    if not os.path.exists("./input"):
        os.makedirs("./input", exist_ok=True)
        fno_logger.info("created directory \"./input\"")
    if not os.path.exists("./output"):
        os.makedirs("./output", exist_ok=True)
        fno_logger.info("created directory \"./output\"")
    if not os.path.exists("./processed"):
        os.makedirs("./processed", exist_ok=True)
        fno_logger.info("created directory \"./processed\"")
    
    yield


app = main()
templates = Jinja2Templates(directory="templates/")

job_queue: list[Job] = []
clients: list[WebSocket] = []


@app.websocket("/ws/jobs")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)
    await websocket.send_text(json.dumps([job.__dict__ for job in job_queue]))
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        clients.remove(websocket)


@app.websocket("/ws/history")
async def websocket_history(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            jobs = []
            async with aiosqlite.connect("jobs_history.db") as db:
                async with db.execute("SELECT * FROM jobs_history ORDER BY date DESC, finish_time DESC") as cursor:
                    columns = [column[0] for column in cursor.description]
                    async for row in cursor:
                        job_dict = dict(zip(columns, row))
                        if 'series_uid_list' in job_dict and job_dict['series_uid_list']:
                            uids: str = job_dict['series_uid_list']
                            if ',' in uids:
                                job_dict['series_uid_list'] = uids.split(',')
                            else:
                                job_dict["series_uid_list"] = [uids]
                        jobs.append(job_dict)
            await websocket.send_text(json.dumps(jobs))
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        fno_logger.info("history client disconnected")
            

@app.get("/", include_in_schema=False)
def home_redirect():
    return RedirectResponse(url="/submit")


@app.get("/submit", response_class=HTMLResponse)
def display_form(request: Request):
    return templates.TemplateResponse("form.html", context={"request": request})


@app.get("/history", response_class=HTMLResponse)
def display_history(request: Request):
    return templates.TemplateResponse("history.html", {"request": request})


async def broadcast_job_queue(current_job=None):
    job_data = {
        "current_job": current_job.__dict__ if current_job else None,
        "pending_jobs": [job.__dict__ for job in job_queue]}
    fno_logger.info(f"broadcasting {len(job_data['pending_jobs'])} jobs to html queue")
    for client in clients:
        try:
            await client.send_text(json.dumps(job_data))
        except Exception as e:
            fno_logger.error(f"failed to send to a client: {e}")
            clients.remove(client)


@app.post("/submit", response_class=HTMLResponse)
async def handle_form(request: Request, 
                pacs_select: str = Form(...), 
                series_uids: str = Form(...),
                process_select: str = Form(...), 
                notify_email: str = Form(...)):
    
    request_id = "".join(random.choices(string.ascii_lowercase + string.digits, k=10))
    pacs_ae, pacs_ip, pacs_port = utils.split_pacs_fields(pacs_select)
    cleaned_uids = series_uids.replace("\r\n", "").replace("\n", "").strip().split(",")
    datetime_now = datetime.now()
    new_job = Job(request_id=request_id,
                  pacs={"ip": pacs_ip, "port": pacs_port, "aetitle": pacs_ae},
                  process_name=process_select,
                  notify_email=notify_email,
                  series_uid_list=cleaned_uids,
                  date=datetime_now.strftime("%Y-%m-%d"))
    job_queue.append(new_job)
    fno_logger.info(f"added new job")
    fno_logger.debug(utils.format_job_string(new_job, level=1))
    await broadcast_job_queue()
    fno_logger.debug("job queue table updated")
    return JSONResponse(content={"message": "Job submitted"})
    
    
@repeat_every(seconds=15)
async def check_queue():
    fno_logger.info("checking queue...")
    if len(job_queue) != 0:
        fno_logger.info(f"found {len(job_queue)} jobs")
        current_job = job_queue[0]
        current_job.status = "processing"
        current_job.start_time = datetime.now().strftime("%H:%M:%S")
        await broadcast_job_queue(current_job)
        fno_logger.debug("job queue table updated")
        
        
        number_of_series = None
        if not os.path.exists(f"./processed/{current_job.request_id}"):
            number_of_series = download_dcm(current_job.request_id, current_job.pacs, current_job.series_uid_list)
            fno_logger.info("download process finished")    
        
        # add getting data from ./processed if it exists
        
        if number_of_series != 0:
            output_dir = os.path.join("./output", current_job.request_id)
            os.makedirs(output_dir, exist_ok=True)
            fno_logger.info(f"created output directory \"{current_job.request_id}\"")
            input_dir = os.path.join("./input", current_job.request_id)
            fno_logger.info("starting process...")
            dicom_convert.dcm_convert(input_dir, "mha", output_dir=output_dir)
        
        current_job.status = "done"
        current_job.finish_time = datetime.now().strftime("%H:%M:%S")
        await broadcast_job_queue(current_job)
        fno_logger.debug("job queue table updated")
        
        try:
            await history.write_job_to_db(current_job)
            fno_logger.debug("job written to .db")
            
        except Exception as e:
            fno_logger.error(f"failed to write job to DB: {e}")
            import traceback
            traceback.print_exc()
            
        source_dirpath = f"./input/{current_job.request_id}"
        dest_dirpath = f"./processed/{current_job.request_id}"
        if os.path.exists(dest_dirpath):
            fno_logger.debug(f"directory \"{dest_dirpath}\" exists, overwriting")
            shutil.rmtree(dest_dirpath)
            
        shutil.move(source_dirpath, dest_dirpath)
        fno_logger.debug(f"moved \"{current_job.request_id}\" data to \"./processed/\" ")
        current_job = None
        removed_job = job_queue.pop(0)
        fno_logger.info(f"removed job from queue")
        fno_logger.debug(utils.format_job_string(removed_job, level=1))
    else:
        fno_logger.info("no job to process")
        await broadcast_job_queue()
        fno_logger.debug("job queue table updated")