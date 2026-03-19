from fastapi import APIRouter, HTTPException
from job_store import get_job, JobStatus

router = APIRouter()


@router.get("/results/{job_id}", tags=["results"])
async def results(job_id: str) -> dict:
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    if job.status not in [JobStatus.COMPLETED, JobStatus.FAILED]:
        raise HTTPException(
            status_code=400,
            detail=f"Job {job_id} is still {job.status}. Poll /status first."
        )

    return {
        "job_id": job_id,
        "status": job.status,
        "total_files": job.total_files,
        "migrated": sum(1 for r in job.results if r.migrated),
        "skipped": sum(1 for r in job.results if not r.migrated),
        "results": job.results,
        "errors": job.error,
    }
