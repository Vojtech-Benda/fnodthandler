import aiosqlite
import os
import logging

from src.job import Job

logger = logging.getLogger("uvicorn")

async def init_db():
    async with aiosqlite.connect("jobs_history.db") as db:
        await db.execute('''
                     CREATE TABLE IF NOT EXISTS jobs_history (
                         request_id TEXT PRIMARY KEY,
                         pacs_ae TEXT,
                         pacs_ip TEXT,
                         pacs_port TEXT,
                         task_name TEXT,
                         uid_list TEXT,
                         notify_email TEXT,
                         date TEXT,
                         start_time TEXT,
                         finish_time TEXT,
                         status TEXT
                         )''')
        await db.commit()
        logger.info("created database jobs_history.db")
        
        
async def write_job_to_db(job: Job):
    async with aiosqlite.connect("jobs_history.db") as db:
        await db.execute(
            '''
            INSERT INTO jobs_history (
             request_id, pacs_ae, pacs_ip, pacs_port, task_name, uid_list, notify_email, date, start_time, finish_time, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (
                job.request_id,
                job.pacs['aetitle'], 
                job.pacs['ip'], 
                job.pacs['port'],
                job.task_name,
                ",".join(job.uid_list),
                job.notify_email,
                job.date,
                job.start_time,
                job.finish_time,
                job.status
            )
        )
        await db.commit()
        logger.info("job written to history")
        
        