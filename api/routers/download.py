from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
from job_store import get_job
from s3_client import download_migrated_file
from botocore.exceptions import ClientError

router = APIRouter()


@router.get("/download/{job_id}/{filename}", tags=["download"])
async def download(job_id: str, filename: str) -> PlainTextResponse:

    # ── 1. Validate job exists ──
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    # ── 2. Fetch from S3 ──
    try:
        content = download_migrated_file(job_id, filename)
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchKey":
            raise HTTPException(
                status_code=404,
                detail=f"{filename} not found — it may not have needed migration"
            )
        raise

    # ── 3. Return as downloadable file ──
    migrated_name = filename.replace(".tsx", "_migrated.tsx")

    return PlainTextResponse(
        content=content.decode("utf-8"),
        headers={
            "Content-Disposition": f"attachment; filename={migrated_name}"
        }
    )