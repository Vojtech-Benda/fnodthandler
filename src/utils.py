from .job import Job

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
            f" - {'UIDs:':<16}{job.series_uid_list}\n"
            )
    return job_string