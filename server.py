from fastapi import FastAPI, Request, Form
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, FileResponse
from fastapi.exceptions import HTTPException
from fastapi_utils.tasks import repeat_every
from contextlib import asynccontextmanager
from typing import Optional

import sys
import os
import random
import string
import json
import aiosqlite
import asyncio
from datetime import datetime
from pathlib import Path
import shutil
import zipfile


from src.algorithms import dicom_convert
from src.download_dcm import download_dcm
from src.job import Job
from src import utils
from src import history
from src.logger import setup_logger


fno_logger = setup_logger("fnodthandler")


def server():
    app = FastAPI(lifespan=lifespan)
    app.mount("/static", StaticFiles(directory="static"), name="static")
    app.mount("/src", StaticFiles(directory="src"), name="src")
    return app


@asynccontextmanager
async def lifespan(app: FastAPI):
    await check_queue() # needs to run once to register with lifespan and FastAPI
    # await delete_file()
    app.add_event_handler("startup", check_queue)
    # app.add_event_handler("startup", delete_file)
    
    if not os.path.exists("jobs_history.db"):
        await history.init_db()

    if not os.path.exists("./input"):
        os.makedirs("./input", exist_ok=True)
        fno_logger.info("created directory \"./input\"")
    if not os.path.exists("./output"):
        os.makedirs("./output", exist_ok=True)
        fno_logger.info("created directory \"./output\"")
    
    yield


app = server()
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
                        if 'uid_list' in job_dict and job_dict['uid_list']:
                            uids: str = job_dict['uid_list']
                            if ',' in uids:
                                job_dict['uid_list'] = uids.split(',')
                            else:
                                job_dict["uid_list"] = [uids]
                        jobs.append(job_dict)
            await websocket.send_text(json.dumps(jobs))
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        fno_logger.info("history client disconnected")


@app.websocket("/ws/data")
async def websocket_data(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            job_data = [
                {'request_id': "sn4b4bk6xb", 'process_name': "dcm2mha", 'file_size': 5},
                {'request_id': "vg4vu008te", 'process_name': "dcm2mha", 'file_size': 5}
                ]
            await websocket.send_text(json.dumps(job_data))
            fno_logger.info("job data sent to /data")
            await asyncio.sleep(3)
    except WebSocketDisconnect:
        fno_logger.info("data client disconnected")


@app.get("/", include_in_schema=False)
def home_redirect():
    return RedirectResponse(url="/submit")


@app.get("/submit", response_class=HTMLResponse)
def display_form(request: Request):
    return templates.TemplateResponse("form.html", context={"request": request})


@app.get("/history", response_class=HTMLResponse)
def display_history(request: Request):
    return templates.TemplateResponse("history.html", {"request": request})


@app.get("/data", response_class=HTMLResponse)
def display_data(request: Request):
    return templates.TemplateResponse("data.html", context={"request": request})


@app.get("/data-download/{request_id}")
def download_zip(request_id: str):
    zip_path = Path("./output", f"{request_id}.zip")
    if not zip_path.is_file():
        raise HTTPException(status_code=404, detail="ZIP file not found")
    
    fno_logger.info(f"sending zip file for {request_id}")
    return FileResponse(zip_path, filename=f"{request_id}.zip", 
                        media_type='application/zip', 
                        headers={"Content-Disposition": f'attachment; filename="{request_id}.zip"'})


async def broadcast_job_queue(current_job=None):
    job_data = {
        "current_job": current_job.__dict__ if current_job else None,
        "pending_jobs": [job.__dict__ for job in job_queue]}
    
    if len(job_data['pending_jobs']) != 0:
        fno_logger.info(f"broadcasting {len(job_data['pending_jobs'])} jobs to html queue")
    
    for client in clients:
        try:
            await client.send_text(json.dumps(job_data))
        except Exception as e:
            fno_logger.error(f"failed to send to a client: {e}")
            clients.remove(client)


async def broadcast_files():
    job_data = [
        {'request_id': "sn4b4bk6xb", 'process_name': "dcm2mha"},
        {'request_id': "vg4vu008te", 'process_name': "dcm2mha"}
        ]

    for client in clients:
        try:
            await client.send_text(json.dumps(job_data))
        except Exception as e:
            fno_logger.error(f"failed to send to a client: {e}")
            clients.remove(client)


@app.post("/submit", response_class=JSONResponse)
async def handle_form(
    request: Request,
    pacs_select: str = Form(...),
    uid_list: str = Form(...),
    process_select: str = Form(...),
    notify_email: str = Form(...),
    custom_process_name: Optional[str] = Form(None)
):
    print(custom_process_name)
    request_id = "".join(random.choices(string.ascii_lowercase + string.digits, k=10))
    pacs_ae, pacs_ip, pacs_port = utils.split_pacs_fields(pacs_select)
    cleaned_uids = uid_list.replace("\r\n", "").replace("\n", "").strip().split(",")
    datetime_now = datetime.now()

    new_job = Job(
        request_id=request_id,
        pacs={"ip": pacs_ip, "port": pacs_port, "aetitle": pacs_ae},
        process_name=custom_process_name if custom_process_name else process_select,
        notify_email=notify_email,
        uid_list=cleaned_uids,
        date=datetime_now.strftime("%d-%m-%Y"),
    )

    job_queue.append(new_job)
    fno_logger.info(f"added new job")
    fno_logger.debug(utils.format_job_string(new_job, level=1))
    await broadcast_job_queue()
    fno_logger.debug("job queue table updated")
    return JSONResponse(content={"message": "Job submitted"})


@app.post("/data-prepare/{request_id}")
def prepare_zip(request_id: str):
    output_dir = Path("./output", request_id)
    zip_path = Path("./output", f"{request_id}.zip")
    
    if zip_path.exists():
        fno_logger.info(f"zip file for {request_id} exists")
        return
    
    if not output_dir.exists():
        raise HTTPException(status_code=404, detail="Output not found")
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(output_dir):
            for file in files:
                fullpath = os.path.join(root, file)
                arcname = os.path.relpath(fullpath, output_dir)
                zipf.write(fullpath, arcname=arcname)
    
    fno_logger.info(f"written zipfile {zip_path}")

@repeat_every(seconds=15)
async def check_queue():
    fno_logger.info("checking queue...")
    if len(job_queue) != 0:
        fno_logger.info(f"found {len(job_queue)} jobs")
        current_job = job_queue.pop(0)
        current_job.status = "downloading"
        current_job.start_time = datetime.now().strftime("%H:%M:%S")
        
        await broadcast_job_queue(current_job)
        fno_logger.debug("job queue table updated")
    
        # check for previously downloaded studies/series
        # download all/missing data
        missing_uids = [uid for uid in current_job.uid_list 
                        if not os.path.exists(os.path.join("./input", uid))]
        code = 0
        if len(missing_uids) != 0:
            fno_logger.debug(f"downloading {",\n".join(missing_uids)} data")
            code = download_dcm(current_job.request_id, current_job.pacs, missing_uids)
        else:
            fno_logger.debug(f"all {current_job.request_id} data found in ./input")
        
        if code == -1:
            current_job.status == "fail"
            
        # 0 - all is good
        # 1 - some data might be missing, ie not found on PACS
        # -1 - none were downloaded when needed
        #FIXME: improve the return codes
        if code == 0 or code == 1:
            output_dir = f"./output/{current_job.request_id}"
            fno_logger.debug(f"creating output directory \"{current_job.request_id}\"")
            os.makedirs(output_dir, exist_ok=True)
            
            data_paths = [os.path.join("./input", uid) for uid in current_job.uid_list]
        
            current_job.status = "processing"
            await broadcast_job_queue(current_job)    
            fno_logger.info(f"starting process {current_job.process_name}...")
            cond = dicom_convert.dcm_convert(data_paths, "mha", output_dir=output_dir)
        
        if cond == 0:
            current_job.status = "done"
        elif cond == -1:
            current_job.status == "fail"
        
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
        
        # send email about finished process
        utils.send_email(current_job)
            
        fno_logger.info(f"removed job from queue")
        fno_logger.debug(utils.format_job_string(current_job, level=1))
    else:
        fno_logger.info("no job to process")
        await broadcast_job_queue()
        fno_logger.debug("job queue table updated")


@repeat_every(seconds=10, wait_first=10)
def delete_file():
    check_dir = "./tes"
    files = os.listdir(check_dir)
    print(files)
    if len(files) == 0:
        return
    for f in files:
        
        path = Path(check_dir + "/" + f)
        if path.is_dir():
            shutil.rmtree(path)
            print(f"removing directory: {path}")
        elif path.is_file():
            os.remove(path)
            print(f"removing file: {path}")
        else:
            print(f"unable to remove file/directory: {path}")
