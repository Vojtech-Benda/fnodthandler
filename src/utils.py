import os
import smtplib, ssl
from email.message import EmailMessage
import zipfile
from pathlib import Path

from src.job import Job
from src.logger import setup_logger
from src.process_result import StatusCodes

fno_logger = setup_logger("fnodthandler")

def split_pacs_fields(pacs_fields: str):
    tokens = pacs_fields.split('-')
    return tokens[0], tokens[1], tokens[2]


def format_job_string(job: Job, level: int = 0):
    """Print Job object in readable form

    Args:
        job (Job): Job object.
        level (int, optional): Print level, 0 (basic), 1 (verbose). Defaults to 0.
    """
    job_string = (
        f"{'Request ID:':<19}{job.request_id}\n"
        f" - {'Date added:':<16}{job.date}\n"
        f" - {'Start time:':<16}{job.start_time}\n"
        f" - {'Finish time':<16}{job.finish_time}\n"
        f" - {'Status:':<16}{job.status}\n"
        )
    
    if level == 1:
        job_string += (
            f" - {'Process:':<16}{job.process_name}\n"
            f" - {'Notify email:':<16}{job.notify_email}\n"
            f" - {'UIDs:':<16}{job.uid_list}\n"
            )
    return job_string


def send_email(job: Job):
    sender_email = os.getenv("SENDER_EMAIL_ADDRESS")
    sender_email_pw = os.getenv("SENDER_EMAIL_PASSWORD")
    
    msg = EmailMessage()
    msg['Subject'] = f"Dokončení procesu {job.request_id} - {job.process_name}" 
    msg['From'] = sender_email
    msg['To'] = job.notify_email
    
    message = f"""\
Žádost {job.request_id} - {job.process_name} ze dne {job.date} je dokončena.
PACS: {job.pacs['aetitle']} - {job.pacs['ip']}:{job.pacs['port']}
Začátek: {job.start_time}
Konec: {job.finish_time}
Stav: {job.status}
Detail stavu: {job.status_detail}

Zpracované DICOM UID:\n{",\n".join(job.uid_list)}

V případě problémů nebo dotazů se obraťte na vojtech.benda@fno.cz nebo fnodthandlerdev@gmail.com.

Tato zpráva byla vytvořena automaticky. Neodpovídejte na ni.
"""

    msg.set_content(message)
    msg.set_charset("utf-8")
    
    context = ssl.create_default_context()
    
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(sender_email, sender_email_pw)
        server.send_message(msg)
    

def zip_data(request_id: str):
    output_dir = Path("./output", request_id)
    zip_path = Path("./output", f"{request_id}.zip")
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(output_dir):
            for file in files:
                fullpath = os.path.join(root, file)
                arcname = os.path.relpath(fullpath, output_dir)
                zipf.write(fullpath, arcname=arcname)
        zipf.close()
        file_size = os.stat(zip_path).st_size / 1_000_000 # bytes to MB
    
    return file_size