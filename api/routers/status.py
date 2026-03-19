from fastapi import APIRouter, HTTPException
from job_store import get_job

router = APIRouter()


@router.get("/status/{job_id}", tags=["status"])
async def status(job_id: str) -> dict:
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    return {
        "job_id": job_id,
        "status": job.status,
        "total_files": job.total_files,
        "processed": job.processed,
        "progress_percent": round((job.processed / job.total_files) * 100) if job.total_files > 0 else 0,
        "results": job.results,
        "errors": job.error,
    }
