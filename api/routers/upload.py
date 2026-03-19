from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Annotated
from job_store import create_job
from s3_client import upload_file

router = APIRouter()


@router.post("/upload/", tags=["upload"])
async def upload(files: Annotated[list[UploadFile], File(description="multiple files")]) -> dict:
    for f in files:
        if not f.filename.endswith(".tsx"):
            raise HTTPException(status_code=400, detail=f"{f.filename} is not a .tsx file")

    filenames = [f.filename for f in files]
    job_id = create_job(filenames)

    for f in files:
        content = await f.read()
        upload_file(job_id, f.filename, content)

    return {
        "job_id": job_id,
        "files_uploaded": len(files),
        "filenames": filenames
    }
