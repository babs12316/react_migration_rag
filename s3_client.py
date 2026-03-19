import boto3
from dotenv import load_dotenv
import os

load_dotenv()

UPLOAD_BUCKET = "migration-upload"
MIGRATED_BUCKET = "migration-results"

s3 = boto3.client(
    "s3",
    endpoint_url=os.getenv("AWS_ENDPOINT_URL"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name="us-east-1"
)


def upload_file(job_id: str, filename: str, content: bytes) -> str:
    key = f"{job_id}/{filename}"
    s3.put_object(
        Bucket=UPLOAD_BUCKET,
        Key=key,
        Body=content,
        ContentType="text/plain"
    )
    return key


def list_files(job_id: str) -> list[str]:
    """Returns filenames uploaded for a given job."""
    response = s3.list_objects_v2(
        Bucket=UPLOAD_BUCKET,
        Prefix=f"{job_id}/"
    )
    if "Contents" not in response:
        return []
    return [obj["Key"].split("/")[-1] for obj in response["Contents"]]


def download_file(job_id: str, filename: str) -> bytes:
    """Download a file from S3 and return its bytes."""
    response = s3.get_object(
        Bucket=UPLOAD_BUCKET,
        Key=f"{job_id}/{filename}"
    )
    return response["Body"].read()


def upload_migrated_file(job_id: str, filename: str, content: str) -> str:
    """Upload migrated file to results bucket. Returns S3 key."""
    migrated_name = filename.replace(".tsx", "_migrated.tsx")
    key = f"{job_id}/{migrated_name}"
    s3.put_object(
        Bucket=MIGRATED_BUCKET,
        Key=key,
        Body=content.encode("utf-8"),
        ContentType="text/plain",
    )
    return key


def download_migrated_file(job_id: str, filename: str) -> bytes:
    """Fetch migrated file content from S3 as a string."""
    key = f"{job_id}/{filename.replace('.tsx', '_migrated.tsx')}"
    response = s3.get_object(Bucket=MIGRATED_BUCKET, Key=key)
    return response["Body"].read()
