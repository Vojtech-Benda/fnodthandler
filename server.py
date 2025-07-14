from fastapi import FastAPI, Request
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, FileResponse
from fastapi.exceptions import HTTPException
from fastapi_utils.tasks import repeat_every
from contextlib import asynccontextmanager

import os
import glob
import random
import string
import json
import aiosqlite
import asyncio
from datetime import datetime
from pathlib import Path
import traceback
from typing import Callable

from src.task_result import TaskResult, StatusCodes

from src.download_dcm import download_dcm
from src.job import Job, ProcessedData
from src import utils
from src import history
from src.task import TaskDispatcher
import logging

logger = logging.getLogger("uvicorn")

# logger = setup_logger("fnodthandler")


def server():
    app = FastAPI(lifespan=lifespan)
    app.mount("/static", StaticFiles(directory="static"), name="static")
    return app


@asynccontextmanager
async def lifespan(app: FastAPI):
    await check_queue() # needs to run once to register with lifespan and FastAPI
    await check_output_data()
    app.add_event_handler("startup", check_queue)
    app.add_event_handler("startup", check_output_data)
    
    if not os.path.exists("jobs_history.db"):
        await history.init_db()

    if not os.path.exists("./input"):
        os.makedirs("./input", exist_ok=True)
        logger.info("created directory \"./input\"")
    if not os.path.exists("./output"):
        os.makedirs("./output", exist_ok=True)
        logger.info("created directory \"./output\"")
    
    yield


app = server()
templates = Jinja2Templates(directory="templates/")

job_queue: list[Job] = []
output_data: list[ProcessedData] = []
clients_jobs: list[WebSocket] = []
clients_history: list[WebSocket] = []
clients_data: list[WebSocket] = []
task_dispatcher = TaskDispatcher()
task_dispatcher.register_tasks()


@app.get('/task_options/{option_name}.html', response_class=HTMLResponse)
async def get_option_file(option_name: str):
    if option_name not in task_dispatcher.tasks:
        raise HTTPException(status_code=404, detail=f"option not allowed: {option_name}")
    
    filepath = Path("templates", "task_options", f"{option_name}.html")
    if not filepath.exists() or not filepath.is_file():
        raise HTTPException(status_code=404, detail=f"HTML options file not found: {option_name}")
    
    return FileResponse(filepath, media_type="text/html")


@app.websocket("/ws/jobs")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients_jobs.append(websocket)
    await websocket.send_text(json.dumps([job.__dict__ for job in job_queue]))
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        clients_jobs.remove(websocket)


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
            await asyncio.sleep(15)
    except WebSocketDisconnect:
        logger.info("history client disconnected")


@app.websocket("/ws/data")
async def websocket_data(websocket: WebSocket):
    await websocket.accept()
    clients_data.append(websocket)
    await websocket.send_text(json.dumps([data.__dict__ for data in output_data]))
    try:
        while True:
            await websocket.receive_text()
            logger.debug("updated processed data table /data")
    except WebSocketDisconnect:
        logger.info("data client disconnected")
        clients_data.remove(websocket)


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
    
    logger.info(f"sending zip file for {request_id}")
    return FileResponse(zip_path, filename=f"{request_id}.zip", 
                        media_type='application/zip', 
                        headers={"Content-Disposition": f'attachment; filename="{request_id}.zip"'})


@app.post("/data-delete/{request_id}")
def delete_zip(request_id: str):
    zip_path = Path("./output", f"{request_id}.zip")
    if not zip_path.exists():
        logger.error(f"ZIP file not found: {zip_path}")
        raise HTTPException(status_code=404, detail="ZIP file not found")
    
    try:
        idx = next((i for i, item in enumerate(output_data) if item['request_id'] == request_id), None)
        if idx:
            output_data.pop(idx)
            logger.info(f"removed output for {request_id}")
            os.remove(zip_path)
            logger.info(f"deleted ZIP file: {zip_path}")
    
    except RuntimeError as err:
        logger.error(err)


@app.post("/submit", response_class=JSONResponse)
async def handle_form(request: Request):
    data: dict[str, str] = await request.json()
    request_id = "".join(random.choices(string.ascii_lowercase + string.digits, k=10))
    pacs_ae, pacs_ip, pacs_port = utils.split_pacs_fields(data['pacs_select'])
    cleaned_uids = data['uid_list'].replace("\r\n", "").replace("\n", "").strip().split(",")
    datetime_now = datetime.now()

    new_job = Job(
        request_id=request_id,
        pacs={"ip": pacs_ip, "port": pacs_port, "aetitle": pacs_ae},
        task_name=data['task_select'],
        notify_email=data['notify_email'],
        uid_list=cleaned_uids,
        date=datetime_now.strftime("%Y-%m-%d"),
        additional_options=data['additional_options']
    )

    job_queue.append(new_job)
    logger.info(f"added new job")
    logger.debug(utils.format_job_string(new_job, level=1))
    await broadcast_job_queue()
    return JSONResponse(content={"message": "Job submitted"})


async def process_job(job: Job):
    job.status = "downloading"
    job.start_time = datetime.now().strftime("%H:%M:%S")

    await broadcast_job_queue(job)

    requested_uids = [uid for uid in job.uid_list if not os.path.exists(os.path.join("./input", uid))]
    download_result = TaskResult()
    if len(requested_uids) != 0:
        logger.debug(f"downloading data for:\n{",\n".join(requested_uids)}")
        download_result = download_dcm(job.pacs, requested_uids)
    else:
        logger.debug(f"all {job.request_id} data found in ./input")
        download_result.mark_success(f"all {job.request_id} data in ./input")

    if download_result.is_bad():
        job.status = "fail"
        job.status_detail = "failed downloading dicom data"
        logger.error(download_result.format_result())

    output_dir = Path("./output", job.request_id)
    if download_result.is_good():
        os.makedirs(output_dir, exist_ok=True)
        input_paths = [os.path.join("./input", uid) for uid in job.uid_list]
        job.status = "processing"

        await broadcast_job_queue(job)

        logger.info(f"starting task {job.task_name}...")

        task_func: Callable[..., TaskResult] = task_dispatcher.get_task(job.task_name)
        try:
            task_result: TaskResult = task_func(input_paths, output_dir, **job.additional_options)
        except Exception as exc:
            logger.error(exc)
            
        logger.info(task_result)        
        if task_result.is_good():
            job.status = "done"
        elif task_result.is_bad():
            job.status = "fail"
            job.status_detail = "failed processing data"

    job.finish_time = datetime.now().strftime("%H:%M:%S")

    await broadcast_job_queue(job)

    try:
        await history.write_job_to_db(job)
        logger.debug("job written to database")
    except Exception as e:
        logger.error(f"failed to write job to database: {e}")
        traceback.print_exc()

    logger.debug("sending email")
    utils.send_email(job)

    logger.info("removed job from queue")
    logger.debug(utils.format_job_string(job, level=1))

    utils.write_uid_list(job.uid_list, output_dir)

    logger.debug(f"zipping output data {job.request_id}")
    file_size = utils.zip_data(job.request_id)

    if file_size > 0:
        processed_data = ProcessedData(
            request_id=job.request_id,
            task_name=job.task_name,
            date=job.date,
            finish_time=job.finish_time,
            file_size=f"{file_size:.2f}",
        )
        output_data.insert(0, processed_data)
        await broadcast_zip_files()
    else:
        logger.error(f"error while zipping data {job.request_id}")


async def broadcast_job_queue(current_job=None):
    job_data = {
        "current_job": current_job.__dict__ if current_job else None,
        "pending_jobs": [job.__dict__ for job in job_queue]}
    
    if len(job_data['pending_jobs']) != 0:
        logger.info(f"broadcasting {len(job_data['pending_jobs'])} jobs to html queue")
    
    for client in clients_jobs:
        try:
            await client.send_text(json.dumps(job_data))
        except Exception as e:
            logger.error(f"failed to send to a client: {e}")
            clients_jobs.remove(client)
            
    logger.debug("job queue updated")


async def broadcast_zip_files():
    logger.info(f"broadcasting {len(output_data)} ZIP files")
    
    for client in clients_data:
        try:
            await client.send_text(json.dumps([data.__dict__ for data in output_data]))
        except Exception as e:
            logger.error(f"failed to send ZIP files to client: {e}")
            clients_data.remove(client)


@repeat_every(seconds=15)
async def check_queue():
    logger.info("checking queue...")
    if len(job_queue) != 0:
        logger.info(f"found {len(job_queue)} jobs")
        current_job = job_queue.pop(0)
        await process_job(current_job)
            
    else:
        logger.info("no job to process")
        await broadcast_job_queue()


@repeat_every(seconds=15)
async def check_output_data():
    logger.info("checking output data...")
    
    files = glob.glob('./output/*.zip')
    current_count = len(output_data)

    if current_count != len(files):
        existing_ids = [item.request_id for item in output_data]
        new_ids = [request_id for path in files if (request_id := Path(path).stem) not in existing_ids]
        async with aiosqlite.connect('jobs_history.db') as db:
                    sql_comm = f"SELECT request_id, task_name, date, finish_time FROM jobs_history WHERE request_id IN ({','.join('?'*len(new_ids))}) ORDER BY date DESC, finish_time DESC"
                    async with db.execute(sql_comm, new_ids) as cursor:
                        columns = [column[0] for column in cursor.description]
                        async for row in cursor:
                            data = ProcessedData(
                                request_id=row[0],
                                task_name=row[1],
                                date=row[2],
                                finish_time=row[3]
                                )
                            fs = os.stat(os.path.join("./output", f"{data.request_id}.zip")).st_size / 1_000_000
                            data.file_size = f"{fs:.2f}"
                            output_data.append(data)
        await broadcast_zip_files()
    else:
        logger.info("no new zip files to send")
