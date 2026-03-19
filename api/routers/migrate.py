from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Annotated
from job_store import get_job, JobStatus
from s3_client import list_files
from migration import run_migration_pipeline

router = APIRouter()


@router.post("/migrate/{job_id}", tags=["migrate"])
async def migrate(
    job_id: Annotated[str, "Job ID returned from /upload"],
    background_tasks: BackgroundTasks
) -> dict:

    # ── 1. Validate job exists ──
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    # ── 2. Validate job is in correct state ──
    if job.status != JobStatus.QUEUED:
        raise HTTPException(
            status_code=400,
            detail=f"Job {job_id} is already {job.status}"
        )

    # ── 3. Get filenames from S3 ──
    filenames = list_files(job_id)
    if not filenames:
        raise HTTPException(
            status_code=400,
            detail=f"No files found for job {job_id}"
        )

    # ── 4. Kick off pipeline in background — returns immediately ──
    background_tasks.add_task(run_migration_pipeline, job_id, filenames)

    return {
        "job_id":  job_id,
        "status":  "queued",
        "files":   len(filenames),
        "message": f"Migration started. Poll /status/{job_id} for progress.",
    }