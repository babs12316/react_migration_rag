import uuid
from enum import Enum
from pydantic import BaseModel
from datetime import datetime
from zoneinfo import ZoneInfo

BERLIN = ZoneInfo("Europe/Berlin")


class JobStatus(str, Enum):
    QUEUED = "queued",
    RUNNING = "running",
    FAILED = "failed",
    COMPLETED = "completed"


class JobResult(BaseModel):
    file: str
    issues_found: list[str] = []
    migrated: bool = False


class Job(BaseModel):
    job_id: str
    status: JobStatus
    total_files: int
    processed: int
    created_at: str
    filenames: list[str]
    results: list[JobResult]
    error: list[dict] = []


_jobs: dict[str, Job] = {}


def get_job(job_id: str) -> Job | None:
    return _jobs.get(job_id)


def create_job(filenames: list[str]) -> str:
    job_id = str(uuid.uuid4())[:8]
    _jobs[job_id] = Job(
        job_id=job_id,
        status=JobStatus.QUEUED,
        total_files=len(filenames),
        processed=0,
        created_at=datetime.now(BERLIN).isoformat(),
        filenames=filenames,
        results=[JobResult(file=f) for f in filenames]
    )
    return job_id


def set_running(job_id: str):
    _jobs[job_id].status = JobStatus.RUNNING


def record_file_result(job_id: str, filename: str, issues: list[str], migrated: bool):
    job = _jobs[job_id]
    for result in job.results:
        if result.file == filename:
            result.issues_found = issues
            result.migrated = migrated
            break
    job.processed += 1


def set_complete(job_id: str):
    _jobs[job_id].status = JobStatus.COMPLETED


def record_error(job_id: str, filename: str, error: str):
    job = _jobs[job_id]
    job.error.append({"file": filename, "error": error})
    job.processed += 1
